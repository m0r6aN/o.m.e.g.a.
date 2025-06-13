#!/bin/bash

# OMEGA Immediate Deployment Script 🚀
# Compatible with older Docker Compose versions (no profiles dependency)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Banner
echo -e "${PURPLE}"
cat << "EOF"
   ____  __  __ _____ ____    _    
  / __ \|  \/  | ____/ ___|  / \   
 | |  | | |\/| |  _|| |  _  / _ \  
 | |__| | |  | | |__| |_| |/ ___ \ 
  \____/|_|  |_|_____\____/_/   \_\
                                   
 OMEGA IMMEDIATE DEPLOYMENT
EOF
echo -e "${NC}"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Docker Compose version
check_docker_compose() {
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "Docker Compose not found!"
        exit 1
    fi
    
    version=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    log_info "Docker Compose version: $version"
    
    # Check if version supports profiles (1.28+)
    major=$(echo $version | cut -d. -f1)
    minor=$(echo $version | cut -d. -f2)
    
    if [[ $major -lt 1 ]] || [[ $major -eq 1 && $minor -lt 28 ]]; then
        log_warning "Docker Compose $version detected - using simplified deployment"
        log_warning "For full features, consider upgrading to 1.28+"
        USE_PROFILES=false
    else
        log_success "Docker Compose supports profiles"
        USE_PROFILES=true
    fi
}

# Create environment file if needed
setup_environment() {
    if [[ ! -f ".env" ]]; then
        log_info "Creating .env file..."
        cat > .env << 'EOF'
# OMEGA Environment Configuration
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
CONTEXT7_API_KEY=your_context7_key_here
SERPER_API_KEY=your_serper_key_here

# Infrastructure
REDIS_HOST=redis
REDIS_PORT=6379
REGISTRY_URL=http://agent_registry:9401
HEARTBEAT_INTERVAL=30

# Monitoring
GRAFANA_PASSWORD=omega123
LOG_LEVEL=info
DEBUG=false

# Node Environment
NODE_ENV=production
EOF
        log_warning "Created .env file with template values"
        log_warning "Please update with your actual API keys!"
    fi
}

# Deploy the constellation
deploy_constellation() {
    log_info "Starting OMEGA Constellation deployment..."
    
    # Start infrastructure first
    log_info "Starting infrastructure services..."
    docker-compose up -d redis agent_registry
    
    # Wait for infrastructure
    log_info "Waiting for infrastructure to stabilize..."
    sleep 15
    
    # Check registry health
    local attempts=0
    local max_attempts=30
    
    while [[ $attempts -lt $max_attempts ]]; do
        if curl -sf http://localhost:9401/health >/dev/null 2>&1; then
            log_success "Agent registry is operational!"
            break
        fi
        
        log_info "Waiting for agent registry... (attempt $((attempts+1))/$max_attempts)"
        sleep 2
        ((attempts++))
    done
    
    if [[ $attempts -eq $max_attempts ]]; then
        log_error "Agent registry failed to start!"
        exit 1
    fi
    
    # Deploy all services
    log_info "Deploying all agents and services..."
    docker-compose up -d
    
    log_success "OMEGA Constellation deployed successfully!"
}

# Show status
show_status() {
    echo -e "\n${CYAN}=== OMEGA SYSTEM STATUS ===${NC}"
    
    # Show running containers
    echo -e "\n${YELLOW}Running Services:${NC}"
    docker-compose ps
    
    # Check key endpoints
    echo -e "\n${YELLOW}Service Health:${NC}"
    
    services=("Redis:6379" "Registry:9401" "Orchestrator:9000")
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        if curl -sf "http://localhost:$port" >/dev/null 2>&1 || curl -sf "http://localhost:$port/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $name: ONLINE${NC}"
        else
            echo -e "${RED}❌ $name: OFFLINE${NC}"
        fi
    done
    
    echo -e "\n${PURPLE}🎯 Access Points:${NC}"
    echo -e "${CYAN}🤖 Agent Registry: ${NC}http://localhost:9401"
    echo -e "${CYAN}🎯 Orchestrator: ${NC}http://localhost:9000"
    echo -e "${CYAN}💻 Frontend: ${NC}http://localhost:3000"
    
    if curl -sf "http://localhost:3001" >/dev/null 2>&1; then
        echo -e "${CYAN}📊 Grafana: ${NC}http://localhost:3001 (admin/omega123)"
    fi
}

# Quick test
run_quick_test() {
    log_info "Running quick system test..."
    
    # Test orchestrator
    if curl -sf "http://localhost:9000/health" >/dev/null 2>&1; then
        log_success "Orchestrator: HEALTHY"
        
        # Test task submission
        response=$(curl -s -X POST "http://localhost:9000/tasks" \
            -H "Content-Type: application/json" \
            -d '{
                "task": {
                    "id": "test_001",
                    "name": "System Test",
                    "description": "Quick deployment test",
                    "payload": {"test": true}
                },
                "header": {
                    "source_agent": "deployment_test",
                    "created_at": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'"
                }
            }' 2>/dev/null)
        
        if [[ $? -eq 0 ]]; then
            log_success "Task delegation: WORKING"
        else
            log_warning "Task delegation: NEEDS ATTENTION"
        fi
    else
        log_error "Orchestrator: OFFLINE"
    fi
    
    # Test registry
    if curl -sf "http://localhost:9401/agents" >/dev/null 2>&1; then
        agent_count=$(curl -s "http://localhost:9401/agents" | jq -r '.agents | length' 2>/dev/null || echo "unknown")
        log_success "Agent Registry: $agent_count agents registered"
    else
        log_error "Agent Registry: OFFLINE"
    fi
}

# Enable monitoring (if supported)
enable_monitoring() {
    log_info "Enabling monitoring stack..."
    
    # Uncomment monitoring services in docker-compose.yml
    if command -v sed >/dev/null 2>&1; then
        cp docker-compose.yml docker-compose.yml.backup
        sed -i 's/^  # \(prometheus:\|grafana:\)/  \1/' docker-compose.yml
        sed -i 's/^  #   /    /' docker-compose.yml
        
        log_info "Starting monitoring services..."
        docker-compose up -d prometheus grafana
        
        log_success "Monitoring stack enabled!"
        log_info "Grafana: http://localhost:3001 (admin/omega123)"
        log_info "Prometheus: http://localhost:9090"
    else
        log_warning "Manual editing required to enable monitoring"
        log_info "Uncomment prometheus and grafana services in docker-compose.yml"
    fi
}

# Main menu
show_menu() {
    echo -e "${CYAN}OMEGA Immediate Deployment Menu:${NC}"
    echo "1. Deploy constellation"
    echo "2. Show status"
    echo "3. Run quick test"
    echo "4. Enable monitoring"
    echo "5. View logs"
    echo "6. Cleanup"
    echo "0. Exit"
    echo
    read -p "Select option: " choice
    
    case $choice in
        1) deploy_constellation ;;
        2) show_status ;;
        3) run_quick_test ;;
        4) enable_monitoring ;;
        5) docker-compose logs -f --tail=50 ;;
        6) 
            log_warning "This will stop and remove all containers"
            read -p "Continue? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker-compose down -v
                log_success "Cleanup completed"
            fi
            ;;
        0) exit 0 ;;
        *) log_error "Invalid option" ;;
    esac
}

# Main execution
main() {
    check_docker_compose
    setup_environment
    
    if [[ $# -eq 0 ]]; then
        # Interactive mode
        while true; do
            show_menu
            echo
        done
    else
        # Command mode
        case "$1" in
            "deploy") deploy_constellation ;;
            "status") show_status ;;
            "test") run_quick_test ;;
            "monitor") enable_monitoring ;;
            "logs") docker-compose logs -f --tail=50 ;;
            "cleanup") 
                docker-compose down -v
                log_success "Cleanup completed"
                ;;
            *) 
                log_error "Unknown command: $1"
                echo "Available commands: deploy, status, test, monitor, logs, cleanup"
                exit 1
                ;;
        esac
    fi
}

# Run main function
main "$@"