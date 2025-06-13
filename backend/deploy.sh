#!/bin/bash

# OMEGA Agent Deployment Script - Because We're Professionals! 🚀
# Usage: ./deploy.sh [command] [options]

set -e  # Exit on any error

# Colors for output (because plain text is boring)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art because we're awesome
show_banner() {
    echo -e "${PURPLE}"
    cat << "EOF"
   ____  __  __ _____ ____    _    
  / __ \|  \/  | ____/ ___|  / \   
 | |  | | |\/| |  _|| |  _  / _ \  
 | |__| | |  | | |__| |_| |/ ___ \ 
  \____/|_|  |_|_____\____/_/   \_\
                                   
 Orchestrated Multi-Expert Gen Agents
EOF
    echo -e "${NC}"
}

# Logging functions
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

# Check if required tools are installed
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    command -v docker >/dev/null 2>&1 || missing_tools+=("docker")
    command -v docker-compose >/dev/null 2>&1 || missing_tools+=("docker-compose")
    command -v curl >/dev/null 2>&1 || missing_tools+=("curl")
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install the missing tools and try again."
        exit 1
    fi
    
    log_success "All prerequisites are installed!"
}

# Validate environment variables
check_environment() {
    log_info "Checking environment variables..."
    
    local missing_vars=()
    
    [ -z "$OPENAI_API_KEY" ] && missing_vars+=("OPENAI_API_KEY")
    [ -z "$ANTHROPIC_API_KEY" ] && missing_vars+=("ANTHROPIC_API_KEY")
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_warning "Missing optional environment variables: ${missing_vars[*]}"
        log_info "Some agents may have limited functionality."
    else
        log_success "All environment variables are set!"
    fi
}

# Create environment file if it doesn't exist
setup_environment() {
    if [ ! -f ".env" ]; then
        log_info "Creating .env file from template..."
        cat > .env << EOF
# OMEGA Framework Environment Variables
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
CONTEXT7_API_KEY=your_context7_key_here

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Registry Configuration
REGISTRY_URL=http://agent_registry:9401
HEARTBEAT_INTERVAL=30

# Development Settings
LOG_LEVEL=info
DEBUG=false
EOF
        log_warning "Created .env file with template values. Please update with your actual API keys!"
    fi
}

# Build all agent images
build_agents() {
    log_info "Building all agent images..."
    
    local agents=(
        "orchestrator"
        "code_generator" 
        "capability_matcher"
        "prompt_optimizer"
        "math_solver"
        "research"
        "weather"
    )
    
    for agent in "${agents[@]}"; do
        if [ -d "src/omega/agents/$agent" ]; then
            log_info "Building $agent..."
            docker build -t "omega-$agent:latest" \
                --build-arg AGENT_NAME="$agent" \
                -f "src/omega/agents/$agent/Dockerfile" \
                src/
            log_success "Built $agent successfully!"
        else
            log_warning "Agent directory not found: src/omega/agents/$agent"
        fi
    done
}

# Deploy the full stack
deploy() {
    log_info "Deploying OMEGA agent constellation..."
    
    # Pull base images first
    docker-compose pull redis
    
    # Start infrastructure first
    log_info "Starting infrastructure services..."
    docker-compose up -d redis agent_registry
    
    # Wait for infrastructure to be ready
    log_info "Waiting for infrastructure to be ready..."
    sleep 10
    
    # Health check for registry
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf http://localhost:9401/health >/dev/null 2>&1; then
            log_success "Agent registry is ready!"
            break
        fi
        
        log_info "Waiting for agent registry... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "Agent registry failed to start!"
        exit 1
    fi
    
    # Start all agents
    log_info "Starting all agents..."
    docker-compose up -d
    
    log_success "OMEGA deployment complete!"
    show_status
}

# Show system status
show_status() {
    echo -e "\n${CYAN}=== OMEGA System Status ===${NC}"
    
    # Check running containers
    echo -e "\n${YELLOW}Running Containers:${NC}"
    docker-compose ps
    
    # Check agent registry
    echo -e "\n${YELLOW}Agent Registry Status:${NC}"
    if curl -sf http://localhost:9401/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Agent Registry: ONLINE${NC}"
        echo -e "   🌐 URL: http://localhost:9401"
        echo -e "   📋 Docs: http://localhost:9401/docs"
    else
        echo -e "${RED}❌ Agent Registry: OFFLINE${NC}"
    fi
    
    # Check frontend
    echo -e "\n${YELLOW}Frontend Status:${NC}"
    if curl -sf http://localhost:3000 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend UI: ONLINE${NC}"
        echo -e "   🎨 URL: http://localhost:3000"
    else
        echo -e "${RED}❌ Frontend UI: OFFLINE${NC}"
    fi
    
    echo -e "\n${PURPLE}🚀 OMEGA is ready for action!${NC}"
}

# Clean up everything
cleanup() {
    log_info "Cleaning up OMEGA deployment..."
    
    docker-compose down --volumes --remove-orphans
    docker system prune -f
    
    log_success "Cleanup complete!"
}

# Show help
show_help() {
    echo -e "${CYAN}OMEGA Agent Deployment Script${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  deploy      Deploy the full OMEGA constellation"
    echo "  build       Build all agent images"
    echo "  status      Show system status"
    echo "  cleanup     Stop and remove all containers"
    echo "  logs        Show logs for all services"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy"
    echo "  $0 status"
    echo "  $0 cleanup"
}

# Environment-specific deployment
deploy_environment() {
    local env="${1:-development}"
    
    log_info "Deploying OMEGA in $env mode..."
    
    case "$env" in
        "development")
            docker-compose up -d
            ;;
        "staging")
            docker-compose --profile monitoring up -d
            ;;
        "production")
            docker-compose --profile production --profile monitoring up -d
            ;;
        *)
            log_error "Unknown environment: $env"
            log_info "Valid environments: development, staging, production"
            exit 1
            ;;
    esac
    
    log_success "OMEGA deployed in $env mode!"
}

# Scale specific services
scale_services() {
    local service="$1"
    local replicas="${2:-2}"
    
    log_info "Scaling $service to $replicas replicas..."
    docker-compose up -d --scale "$service=$replicas" "$service"
    log_success "$service scaled to $replicas replicas!"
}

# Backup critical data
backup_data() {
    log_info "Creating backup of OMEGA data..."
    
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup Redis data
    docker exec omega_redis redis-cli BGSAVE
    docker cp omega_redis:/data/dump.rdb "$backup_dir/redis_dump.rdb"
    
    # Backup agent registry data
    docker cp omega_agent_registry:/app/data "$backup_dir/registry_data"
    
    log_success "Backup created in $backup_dir"
}

# Update specific agents
update_agent() {
    local agent_name="$1"
    
    if [ -z "$agent_name" ]; then
        log_error "Agent name is required"
        exit 1
    fi
    
    log_info "Updating $agent_name..."
    
    # Build new image
    docker-compose build "$agent_name"
    
    # Rolling update
    docker-compose up -d --no-deps "$agent_name"
    
    log_success "$agent_name updated successfully!"
}

# Main script logic
main() {
    show_banner
    
    case "${1:-help}" in
        "deploy")
            check_prerequisites
            setup_environment
            check_environment
            build_agents
            deploy_environment "${2:-development}"
            ;;
        "build")
            check_prerequisites
            build_agents
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup
            ;;
        "logs")
            if [ -n "$2" ]; then
                docker-compose logs -f "$2"
            else
                docker-compose logs -f
            fi
            ;;
        "scale")
            scale_services "$2" "$3"
            ;;
        "backup")
            backup_data
            ;;
        "update")
            update_agent "$2"
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run the script
main "$@"