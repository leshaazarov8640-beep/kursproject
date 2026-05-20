FROM golang:1.26-alpine AS builder

WORKDIR /app
COPY go-pcap/go.mod go-pcap/go.sum ./
RUN go mod download

COPY go-pcap/ ./
RUN CGO_ENABLED=0 GOOS=linux go build -o /ids-pcap .

FROM alpine:3.21
RUN apk --no-cache add ca-certificates libpcap
COPY --from=builder /ids-pcap /usr/local/bin/ids-pcap
ENTRYPOINT ["/usr/local/bin/ids-pcap"]
