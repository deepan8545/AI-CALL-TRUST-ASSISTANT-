package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/segmentio/kafka-go"
	_ "github.com/lib/pq"
)

// ScoredCallEvent represents a scored call event from Kafka
type ScoredCallEvent struct {
	CallID          string   `json:"call_id"`
	PhoneNumberHash string   `json:"phone_number_hash"`
	CarrierID       string   `json:"carrier_id"`
	Timestamp       string   `json:"timestamp"`
	UserRegion      string   `json:"user_region"`
	RiskScore       float64  `json:"risk_score"`
	RiskLabel       string   `json:"risk_label"`
	ReasonCodes     []string `json:"reason_codes"`
	ScoredAt        string   `json:"scored_at"`
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}

func connectDB() (*sql.DB, error) {
	dsn := getEnv("DATABASE_URL", "postgres://call_trust_user:call_trust_pass@localhost:5432/call_trust?sslmode=disable")
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}
	db.SetMaxOpenConns(10)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}
	log.Println("[DB] Connected to PostgreSQL")
	return db, nil
}

func writeProcessedStatus(db *sql.DB, event ScoredCallEvent) error {
	query := `
		INSERT INTO model_decisions (call_id, rules_score, final_score, final_label, explanation, created_at)
		SELECT $1::uuid, $2, $2, $3, $4, NOW()
		WHERE EXISTS (SELECT 1 FROM call_events WHERE id = $1::uuid)
	`
	explanation := fmt.Sprintf("Processed by event worker. Reason codes: %v", event.ReasonCodes)
	_, err := db.Exec(query, event.CallID, event.RiskScore, event.RiskLabel, explanation)
	if err != nil {
		// If call_id doesn't exist in call_events, log and skip (not a fatal error)
		log.Printf("[DB] Could not write decision for %s (call may not exist in DB): %v", event.CallID, err)
		return nil
	}
	log.Printf("[DB] Wrote processed status for call %s", event.CallID)
	return nil
}

func main() {
	log.Println("=== AI Call Trust Assistant — Event Worker (Go) ===")

	// --- Connect to PostgreSQL ---
	db, err := connectDB()
	if err != nil {
		log.Printf("[DB] WARNING: %v — will log events only", err)
	} else {
		defer db.Close()
	}

	// --- Kafka consumer setup ---
	brokers := getEnv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
	topic := getEnv("KAFKA_TOPIC_CALL_SCORED", "call.scored")
	groupID := getEnv("KAFKA_CONSUMER_GROUP", "event-worker-group")

	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:        []string{brokers},
		Topic:          topic,
		GroupID:        groupID,
		MinBytes:       1e3,  // 1KB
		MaxBytes:       10e6, // 10MB
		CommitInterval: time.Second,
		StartOffset:    kafka.LastOffset,
	})
	defer reader.Close()

	log.Printf("[Kafka] Consuming from topic '%s' (broker: %s, group: %s)", topic, brokers, groupID)

	// --- Graceful shutdown ---
	ctx, cancel := context.WithCancel(context.Background())
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigChan
		log.Printf("[Worker] Received signal %v — shutting down", sig)
		cancel()
	}()

	// --- Consume loop ---
	processed := 0
	for {
		msg, err := reader.ReadMessage(ctx)
		if err != nil {
			if ctx.Err() != nil {
				break // shutdown requested
			}
			log.Printf("[Kafka] Read error: %v", err)
			time.Sleep(time.Second)
			continue
		}

		var event ScoredCallEvent
		if err := json.Unmarshal(msg.Value, &event); err != nil {
			log.Printf("[Worker] Failed to parse message: %v", err)
			continue
		}

		processed++
		log.Printf("[Worker] #%d | call=%s score=%.2f label=%s reasons=%v",
			processed, event.CallID, event.RiskScore, event.RiskLabel, event.ReasonCodes)

		// Write to PostgreSQL if connected
		if db != nil {
			if err := writeProcessedStatus(db, event); err != nil {
				log.Printf("[Worker] DB write error: %v", err)
			}
		}
	}

	log.Printf("[Worker] Shut down after processing %d events", processed)
}
