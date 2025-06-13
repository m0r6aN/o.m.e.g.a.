#!/bin/bash

# OMEGA Bridge Commander - Enterprise Control Script 🚀
# The ultimate command center for your AI agent constellation

set -e

# Colors for the command bridge
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Bridge ASCII Art
show_bridge_banner() {
    echo -e "${PURPLE}"
    cat << "EOF"
    ╔══════════════════════════════════════════════════════════════╗
    ║                    OMEGA BRIDGE COMMANDER                    ║
    ║                  Enterprise Control Center                   ║
    ╚══════════════════════════════════════════════════════════════╝
    
       ⚡ ORCHESTRATED MULTI-EXPERT GEN AGENTS ⚡
    
    🎯 Mission: Deploy and command the AI agent constellation
    🚀 Status: Ready for interstellar operations
    ⭐ Crew: Standing by for orders, Captain
    
EOF
    echo -e "${NC}"
}

# Logging functions with enhanced style
log_command() {
    echo -e "${WHITE}[BRIDGE COMMAND]${NC} $1"
}

log_info() {
    echo -e "${BLUE}[TACTICAL]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[ALERT]${NC} $1"
}

log_error() {
    echo -e "${RED}[CRITICAL]${NC} $1"
}

log_system() {
    echo -e "${CYAN}[SYSTEM]${NC} $1"
}

# System status display
show_constellation_status() {
    echo -e "\n${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                    OMEGA CONSTELLATION STATUS                 ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    
    # Check Docker and Docker Compose
    if command -v docker >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker Engine: OPERATIONAL${NC}"
    else
        echo -e "${RED}❌ Docker Engine: OFFLINE${NC}"
        return 1
    fi
    
    if command -v docker-compose >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker Compose: OPERATIONAL${NC}"
    else
        echo -e "${RED}❌ Docker Compose: OFFLINE${NC}"
        return 1
    fi
    
    # Check running containers
    echo -e "\n${YELLOW}🤖 AGENT FLEET STATUS:${NC}"
    if docker-compose ps >/dev/null 2>&1; then
        docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" | while IFS= read -r line; do
            if [[ "$line" == *"Up"* ]]; then
                echo -e "${GREEN}✅ $line${NC}"
            elif [[ "$line" == *"Exit"* ]]; then
                echo -e "${RED}❌ $line${NC}"
            else
                echo -e "${CYAN}$line${NC}"
            fi
        done
    else
        echo -e "${YELLOW}⚠️  No containers deployed${NC}"
    fi
    
    # Check key service endpoints
    echo -e "\n${YELLOW}🌟 CORE SERVICES STATUS:${NC}"
    
    services=(
        "Redis Database:6379"
        "Agent Registry:9401"
        "Orchestrator:9000"
        "Monitoring (Grafana):3001"
        "Metrics (Prometheus):9090"
        "Frontend UI:3000"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        if curl -s -f "http://localhost:$port" >/dev/null 2>&1 || curl -s -f "http://localhost:$port/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $name (Port $port): ONLINE${NC}"
        else
            echo -e "${RED}❌ $name (Port $port): OFFLINE${NC}"
        fi
    done
    
    # System resource usage
    echo -e "\n${YELLOW}⚡ SYSTEM RESOURCES:${NC}"
    if command -v docker >/dev/null 2>&1; then
        docker system df --format "table {{.Type}}\t{{.Total}}\t{{.Active}}\t{{.Size}}" | head -4
    fi
    
    echo -e "\n${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                    END STATUS REPORT                         ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}\n"
}

# Enhanced deployment with progress tracking
deploy_constellation() {
    local environment="${1:-development}"
    
    log_command "Initiating OMEGA Constellation deployment in $environment mode"
    
    # Pre-flight checks
    log_info "Conducting pre-flight system checks..."
    
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker not found. Please install Docker and try again."
        exit 1
    fi
    
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "Docker Compose not found. Please install Docker Compose and try again."
        exit 1
    fi
    
    # Check for required files
    required_files=("docker-compose.yml" ".env")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_warning "$file not found. Creating from template..."
            if [[ "$file" == ".env" ]]; then
                create_env_file
            fi
        fi
    done
    
    log_success "Pre-flight checks completed"
    
    # Deployment sequence
    log_info "Starting infrastructure services..."
    docker-compose up -d redis agent_registry
    
    log_info "Waiting for infrastructure to stabilize..."
    sleep 15
    
    # Health check for core services
    log_info "Verifying core services..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf http://localhost:9401/health >/dev/null 2>&1; then
            log_success "Agent registry is operational!"
            break
        fi
        
        log_info "Waiting for agent registry... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "Agent registry failed to start within timeout period"
        exit 1
    fi
    
    # Deploy based on environment
    case "$environment" in
        "development")
            log_info "Deploying development environment..."
            docker-compose up -d
            ;;
        "staging")
            log_info "Deploying staging environment with monitoring..."
            docker-compose --profile monitoring up -d
            ;;
        "production")
            log_info "Deploying full production environment..."
            docker-compose --profile production --profile monitoring up -d
            ;;
        *)
            log_error "Unknown environment: $environment"
            exit 1
            ;;
    esac
    
    log_success "OMEGA Constellation deployed successfully in $environment mode!"
    
    # Post-deployment verification
    sleep 10
    show_constellation_status
    
    # Display access information
    echo -e "\n${PURPLE}🎯 MISSION CONTROL ENDPOINTS:${NC}"
    echo -e "${CYAN}🎛️  Bridge Console (Grafana): ${WHITE}http://localhost:3001${NC} (admin/omega123)"
    echo -e "${CYAN}📊  Metrics Dashboard: ${WHITE}http://localhost:9090${NC}"
    echo -e "${CYAN}🤖  Agent Registry: ${WHITE}http://localhost:9401${NC}"
    echo -e "${CYAN}🎯  Orchestrator: ${WHITE}http://localhost:9000${NC}"
    echo -e "${CYAN}💻  Frontend UI: ${WHITE}http://localhost:3000${NC}"
    
    log_success "OMEGA Enterprise Platform is fully operational! 🚀"
}

# Create environment file
create_env_file() {
    log_info "Creating enterprise environment configuration..."
    
    cat > .env << 'EOF'
# OMEGA Enterprise Environment Configuration 🚀
# Production-ready settings for the AI agent constellation

# API Keys (Replace with your actual keys)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
CONTEXT7_API_KEY=your_context7_key_here
SERPER_API_KEY=your_serper_key_here

# Infrastructure Settings
REDIS_HOST=redis
REDIS_PORT=6379
REGISTRY_URL=http://agent_registry:9401
HEARTBEAT_INTERVAL=30

# Monitoring & Observability
GRAFANA_PASSWORD=omega123
PROMETHEUS_RETENTION=200h
LOG_LEVEL=info
DEBUG=false

# Application Settings
NODE_ENV=production
BUILD_TARGET=production

# Security Settings (Customize for production)
JWT_SECRET=your_jwt_secret_here
ENCRYPTION_KEY=your_encryption_key_here

# Performance Tuning
WORKER_PROCESSES=4
MAX_CONNECTIONS=1000
TIMEOUT_SECONDS=30

# Optional: External Services
POSTGRES_URL=postgresql://user:pass@localhost:5432/omega
ELASTICSEARCH_URL=http://localhost:9200
EOF
    
    log_warning "Environment file created with template values"
    log_warning "Please update .env with your actual API keys before deployment"
}

# Live system monitoring
monitor_constellation() {
    log_command "Initiating live constellation monitoring..."
    
    # Check if monitoring stack is running
    if ! curl -sf http://localhost:3001 >/dev/null 2>&1; then
        log_warning "Grafana not detected. Deploying monitoring stack..."
        docker-compose --profile monitoring up -d prometheus grafana loki
        sleep 15
    fi
    
    echo -e "\n${PURPLE}🔍 LIVE MONITORING DASHBOARD${NC}"
    echo -e "${CYAN}================================${NC}"
    
    # Real-time metrics loop
    while true; do
        clear
        show_bridge_banner
        
        # Current timestamp
        echo -e "${YELLOW}📅 $(date '+%Y-%m-%d %H:%M:%S UTC')${NC}\n"
        
        # Quick status check
        echo -e "${CYAN}🚀 QUICK STATUS CHECK:${NC}"
        
        # Agent health checks
        agents=("orchestrator:9000" "code_generator:9014" "capability_matcher:9008")
        
        for agent in "${agents[@]}"; do
            IFS=':' read -r name port <<< "$agent"
            if curl -sf "http://localhost:$port/health" >/dev/null 2>&1; then
                echo -e "${GREEN}✅ $name: HEALTHY${NC}"
            else
                echo -e "${RED}❌ $name: UNHEALTHY${NC}"
            fi
        done
        
        # System metrics
        echo -e "\n${CYAN}📊 SYSTEM METRICS:${NC}"
        
        # Docker stats (if available)
        if command -v docker >/dev/null 2>&1; then
            echo -e "${YELLOW}Container Resource Usage:${NC}"
            timeout 2 docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -6
        fi
        
        echo -e "\n${CYAN}Press Ctrl+C to exit monitoring${NC}"
        echo -e "${CYAN}================================${NC}"
        
        sleep 10
    done
}

# Agent fleet management
manage_agent_fleet() {
    local action="$1"
    local agent="$2"
    local replicas="${3:-1}"
    
    case "$action" in
        "scale")
            if [[ -z "$agent" ]]; then
                log_error "Agent name required for scaling"
                exit 1
            fi
            
            log_command "Scaling $agent to $replicas replicas..."
            docker-compose up -d --scale "$agent=$replicas" "$agent"
            log_success "$agent scaled to $replicas replicas!"
            ;;
        "restart")
            if [[ -z "$agent" ]]; then
                log_error "Agent name required for restart"
                exit 1
            fi
            
            log_command "Restarting $agent..."
            docker-compose restart "$agent"
            log_success "$agent restarted successfully!"
            ;;
        "logs")
            if [[ -z "$agent" ]]; then
                log_info "Showing logs for all services..."
                docker-compose logs -f --tail=100
            else
                log_info "Showing logs for $agent..."
                docker-compose logs -f --tail=100 "$agent"
            fi
            ;;
        "update")
            if [[ -z "$agent" ]]; then
                log_error "Agent name required for update"
                exit 1
            fi
            
            log_command "Updating $agent with zero downtime..."
            docker-compose build "$agent"
            docker-compose up -d --no-deps "$agent"
            log_success "$agent updated successfully!"
            ;;
        *)
            log_error "Unknown fleet action: $action"
            log_info "Available actions: scale, restart, logs, update"
            exit 1
            ;;
    esac
}

# System maintenance
system_maintenance() {
    local action="$1"
    
    case "$action" in
        "backup")
            log_command "Creating system backup..."
            
            local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
            mkdir -p "$backup_dir"
            
            # Backup Redis data
            if docker-compose ps redis | grep -q "Up"; then
                log_info "Backing up Redis data..."
                docker exec omega_redis redis-cli BGSAVE
                sleep 5
                docker cp omega_redis:/data/dump.rdb "$backup_dir/redis_dump.rdb"
            fi
            
            # Backup agent registry data
            if docker-compose ps agent_registry | grep -q "Up"; then
                log_info "Backing up agent registry data..."
                docker cp omega_agent_registry:/app/data "$backup_dir/registry_data" 2>/dev/null || true
            fi
            
            # Backup configuration
            cp docker-compose.yml "$backup_dir/"
            cp .env "$backup_dir/" 2>/dev/null || true
            
            log_success "Backup created in $backup_dir"
            ;;
        "cleanup")
            log_command "Performing system cleanup..."
            
            # Remove unused containers, networks, images
            docker system prune -f
            
            # Remove unused volumes (with confirmation)
            read -p "Remove unused volumes? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker volume prune -f
            fi
            
            log_success "System cleanup completed!"
            ;;
        "health-check")
            log_command "Running comprehensive health check..."
            
            echo -e "\n${CYAN}🏥 OMEGA HEALTH DIAGNOSTIC${NC}"
            echo -e "${CYAN}===========================${NC}"
            
            # Check all agent health endpoints
            agents=("orchestrator:9000" "code_generator:9014" "capability_matcher:9008" "prompt_optimizer:9006")
            
            for agent in "${agents[@]}"; do
                IFS=':' read -r name port <<< "$agent"
                echo -e "\n${YELLOW}Checking $name...${NC}"
                
                if curl -sf "http://localhost:$port/health" >/dev/null 2>&1; then
                    health_data=$(curl -s "http://localhost:$port/health" | jq -r '.')
                    echo -e "${GREEN}✅ $name: HEALTHY${NC}"
                    echo "$health_data" | jq .
                else
                    echo -e "${RED}❌ $name: UNHEALTHY${NC}"
                fi
            done
            
            log_success "Health check completed!"
            ;;
        *)
            log_error "Unknown maintenance action: $action"
            log_info "Available actions: backup, cleanup, health-check"
            exit 1
            ;;
    esac
}

# Quick test suite
run_quick_tests() {
    log_command "Running OMEGA quick test suite..."
    
    echo -e "\n${CYAN}🧪 OMEGA QUICK TEST SUITE${NC}"
    echo -e "${CYAN}==========================${NC}"
    
    # Test 1: Service availability
    echo -e "\n${YELLOW}Test 1: Service Availability${NC}"
    services=("redis:6379" "agent_registry:9401" "orchestrator:9000")
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        if curl -sf "http://localhost:$port" >/dev/null 2>&1 || curl -sf "http://localhost:$port/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $name: AVAILABLE${NC}"
        else
            echo -e "${RED}❌ $name: UNAVAILABLE${NC}"
        fi
    done
    
    # Test 2: Agent registration
    echo -e "\n${YELLOW}Test 2: Agent Registration${NC}"
    if curl -sf "http://localhost:9401/agents" >/dev/null 2>&1; then
        agent_count=$(curl -s "http://localhost:9401/agents" | jq -r '.agents | length')
        echo -e "${GREEN}✅ Registry accessible, $agent_count agents registered${NC}"
    else
        echo -e "${RED}❌ Cannot access agent registry${NC}"
    fi
    
    # Test 3: Task delegation
    echo -e "\n${YELLOW}Test 3: Task Delegation${NC}"
    if curl -sf "http://localhost:9000/health" >/dev/null 2>&1; then
        response=$(curl -s -X POST "http://localhost:9000/tasks" \
            -H "Content-Type: application/json" \
            -d '{
                "task": {
                    "id": "test_task_001",
                    "name": "Health Check Task",
                    "description": "Simple health check task for testing",
                    "payload": {"test": true}
                },
                "header": {
                    "source_agent": "test_client",
                    "created_at": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'"
                }
            }' 2>/dev/null)
        
        if [[ $? -eq 0 ]]; then
            echo -e "${GREEN}✅ Task delegation successful${NC}"
        else
            echo -e "${RED}❌ Task delegation failed${NC}"
        fi
    else
        echo -e "${RED}❌ Orchestrator not available${NC}"
    fi
    
    # Test 4: Monitoring stack
    echo -e "\n${YELLOW}Test 4: Monitoring Stack${NC}"
    if curl -sf "http://localhost:9090/api/v1/targets" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Prometheus: OPERATIONAL${NC}"
    else
        echo -e "${RED}❌ Prometheus: UNAVAILABLE${NC}"
    fi
    
    if curl -sf "http://localhost:3001/api/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Grafana: OPERATIONAL${NC}"
    else
        echo -e "${RED}❌ Grafana: UNAVAILABLE${NC}"
    fi
    
    echo -e "\n${CYAN}🎯 Test suite completed!${NC}"
    log_success "OMEGA quick tests finished!"
}

# Show comprehensive help
show_help() {
    echo -e "${CYAN}OMEGA Bridge Commander - Enterprise Control Center${NC}"
    echo ""
    echo -e "${WHITE}USAGE:${NC}"
    echo "  $0 [COMMAND] [OPTIONS]"
    echo ""
    echo -e "${WHITE}DEPLOYMENT COMMANDS:${NC}"
    echo "  deploy [env]         Deploy OMEGA constellation"
    echo "                       env: development|staging|production (default: development)"
    echo "  status              Show comprehensive system status"
    echo "  build               Build all agent images"
    echo "  cleanup             Stop and remove all containers"
    echo ""
    echo -e "${WHITE}FLEET MANAGEMENT:${NC}"
    echo "  fleet scale <agent> <replicas>  Scale specific agent"
    echo "  fleet restart <agent>           Restart specific agent"
    echo "  fleet logs [agent]              Show logs (all or specific agent)"
    echo "  fleet update <agent>            Update agent with zero downtime"
    echo ""
    echo -e "${WHITE}MONITORING & MAINTENANCE:${NC}"
    echo "  monitor             Start live constellation monitoring"
    echo "  test                Run quick test suite"
    echo "  maintenance backup  Create system backup"
    echo "  maintenance cleanup Clean up unused resources"
    echo "  maintenance health  Run comprehensive health check"
    echo ""
    echo -e "${WHITE}EXAMPLES:${NC}"
    echo "  $0 deploy production             # Deploy full production stack"
    echo "  $0 fleet scale orchestrator 3   # Scale orchestrator to 3 replicas"
    echo "  $0 fleet logs code_generator     # Show code generator logs"
    echo "  $0 monitor                       # Start live monitoring"
    echo "  $0 test                         # Run quick tests"
    echo ""
    echo -e "${WHITE}ENDPOINTS (after deployment):${NC}"
    echo -e "${CYAN}  🎛️  Bridge Console: ${WHITE}http://localhost:3001${NC} (admin/omega123)"
    echo -e "${CYAN}  📊  Metrics: ${WHITE}http://localhost:9090${NC}"
    echo -e "${CYAN}  🤖  Registry: ${WHITE}http://localhost:9401${NC}"
    echo -e "${CYAN}  🎯  Orchestrator: ${WHITE}http://localhost:9000${NC}"
    echo -e "${CYAN}  💻  Frontend: ${WHITE}http://localhost:3000${NC}"
}

# Performance benchmarking
run_performance_benchmark() {
    log_command "Running OMEGA performance benchmark..."
    
    echo -e "\n${CYAN}⚡ OMEGA PERFORMANCE BENCHMARK${NC}"
    echo -e "${CYAN}===============================${NC}"
    
    # Check if orchestrator is available
    if ! curl -sf "http://localhost:9000/health" >/dev/null 2>&1; then
        log_error "Orchestrator not available for benchmarking"
        exit 1
    fi
    
    # Test 1: Response time benchmark
    echo -e "\n${YELLOW}Test 1: Response Time Benchmark${NC}"
    
    total_time=0
    successful_requests=0
    failed_requests=0
    
    for i in {1..10}; do
        echo -n "Request $i/10... "
        
        start_time=$(date +%s.%N)
        
        response=$(curl -s -w "%{http_code}" -X POST "http://localhost:9000/tasks" \
            -H "Content-Type: application/json" \
            -d '{
                "task": {
                    "id": "benchmark_'$i'",
                    "name": "Benchmark Task",
                    "description": "Performance benchmark task",
                    "payload": {"benchmark": true, "iteration": '$i'}
                },
                "header": {
                    "source_agent": "benchmark_client",
                    "created_at": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'"
                }
            }' 2>/dev/null)
        
        end_time=$(date +%s.%N)
        duration=$(echo "$end_time - $start_time" | bc -l)
        
        http_code="${response: -3}"
        
        if [[ "$http_code" == "200" ]]; then
            echo -e "${GREEN}✅ ${duration}s${NC}"
            total_time=$(echo "$total_time + $duration" | bc -l)
            ((successful_requests++))
        else
            echo -e "${RED}❌ HTTP $http_code${NC}"
            ((failed_requests++))
        fi
        
        sleep 0.5
    done
    
    if [[ $successful_requests -gt 0 ]]; then
        avg_time=$(echo "scale=3; $total_time / $successful_requests" | bc -l)
        echo -e "\n${CYAN}📊 Results:${NC}"
        echo -e "  Successful requests: ${GREEN}$successful_requests${NC}"
        echo -e "  Failed requests: ${RED}$failed_requests${NC}"
        echo -e "  Average response time: ${YELLOW}${avg_time}s${NC}"
    fi
    
    # Test 2: Concurrent requests
    echo -e "\n${YELLOW}Test 2: Concurrent Request Handling${NC}"
    echo "Sending 5 concurrent requests..."
    
    pids=()
    for i in {1..5}; do
        (
            response=$(curl -s -w "%{http_code}" -X POST "http://localhost:9000/tasks" \
                -H "Content-Type: application/json" \
                -d '{
                    "task": {
                        "id": "concurrent_'$i'",
                        "name": "Concurrent Task '$i'",
                        "description": "Concurrent benchmark task",
                        "payload": {"concurrent": true, "batch": '$i'}
                    },
                    "header": {
                        "source_agent": "concurrent_client",
                        "created_at": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'"
                    }
                }' 2>/dev/null)
            
            http_code="${response: -3}"
            echo "Concurrent request $i: HTTP $http_code"
        ) &
        pids+=($!)
    done
    
    # Wait for all concurrent requests to complete
    for pid in "${pids[@]}"; do
        wait $pid
    done
    
    echo -e "${GREEN}✅ Concurrent request test completed${NC}"
    
    log_success "Performance benchmark completed!"
}

# Emergency procedures
emergency_procedures() {
    local action="$1"
    
    case "$action" in
        "shutdown")
            log_command "EMERGENCY: Initiating controlled shutdown..."
            
            echo -e "${RED}⚠️  EMERGENCY SHUTDOWN INITIATED${NC}"
            echo -e "${YELLOW}Gracefully stopping all agents...${NC}"
            
            docker-compose down --timeout 30
            
            log_success "Emergency shutdown completed"
            ;;
        "restart")
            log_command "EMERGENCY: Initiating system restart..."
            
            echo -e "${YELLOW}⚠️  EMERGENCY RESTART INITIATED${NC}"
            
            # Graceful shutdown
            docker-compose down --timeout 30
            
            # Clean restart
            sleep 5
            docker-compose up -d
            
            log_success "Emergency restart completed"
            ;;
        "reset")
            log_command "EMERGENCY: Initiating system reset..."
            
            echo -e "${RED}⚠️  EMERGENCY RESET INITIATED${NC}"
            echo -e "${YELLOW}This will remove all containers and volumes!${NC}"
            
            read -p "Are you sure? Type 'RESET' to confirm: " -r
            if [[ $REPLY == "RESET" ]]; then
                docker-compose down -v --remove-orphans
                docker system prune -af --volumes
                log_success "Emergency reset completed"
            else
                log_info "Reset cancelled"
            fi
            ;;
        *)
            log_error "Unknown emergency procedure: $action"
            log_info "Available procedures: shutdown, restart, reset"
            exit 1
            ;;
    esac
}

# Main command router
main() {
    show_bridge_banner
    
    case "${1:-help}" in
        "deploy")
            deploy_constellation "${2:-development}"
            ;;
        "status")
            show_constellation_status
            ;;
        "build")
            log_command "Building all agent images..."
            docker-compose build
            log_success "All images built successfully!"
            ;;
        "cleanup")
            log_command "Cleaning up OMEGA deployment..."
            docker-compose down --volumes --remove-orphans
            docker system prune -f
            log_success "Cleanup completed!"
            ;;
        "fleet")
            manage_agent_fleet "$2" "$3" "$4"
            ;;
        "monitor")
            monitor_constellation
            ;;
        "test")
            run_quick_tests
            ;;
        "benchmark")
            run_performance_benchmark
            ;;
        "maintenance")
            system_maintenance "$2"
            ;;
        "emergency")
            emergency_procedures "$2"
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Trap for graceful exit
trap 'echo -e "\n${YELLOW}Bridge Commander shutting down...${NC}"; exit 0' INT TERM

# Execute main function
main "$@"