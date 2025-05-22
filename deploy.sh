#!/bin/bash
# Deployment script for ParallaxMind ADK system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${PROJECT_ID:-"your-project-id"}
REGION=${REGION:-"us-central1"}
ENVIRONMENT=${ENVIRONMENT:-"production"}

echo -e "${BLUE}🚀 Deploying ParallaxMind ADK System${NC}"
echo -e "${BLUE}======================================${NC}"

# Validate prerequisites
check_prerequisites() {
    echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    # Check if ADK CLI is available
    if ! command -v adk &> /dev/null; then
        echo -e "${YELLOW}⚠️  ADK CLI not found. Installing...${NC}"
        pip install google-cloud-aiplatform[adk]
    fi
    
    # Check if logged in to gcloud
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo -e "${RED}❌ Not logged in to gcloud. Please run 'gcloud auth login'.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed!${NC}"
}

# Setup Google Cloud project
setup_project() {
    echo -e "${YELLOW}🔧 Setting up Google Cloud project...${NC}"
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    echo -e "${YELLOW}🔌 Enabling required APIs...${NC}"
    gcloud services enable \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        containerregistry.googleapis.com \
        aiplatform.googleapis.com \
        secretmanager.googleapis.com \
        redis.googleapis.com \
        sql-component.googleapis.com
    
    echo -e "${GREEN}✅ Google Cloud project setup complete!${NC}"
}

# Create secrets
create_secrets() {
    echo -e "${YELLOW}🔐 Creating secrets...${NC}"
    
    # Check if secrets already exist, create if they don't
    if ! gcloud secrets describe parallaxmind-secret --quiet; then
        echo -n "Enter SECRET_KEY: "
        read -s SECRET_KEY
        echo
        echo -n "$SECRET_KEY" | gcloud secrets create parallaxmind-secret --data-file=-
    fi
    
    if ! gcloud secrets describe parallaxmind-db-url --quiet; then
        echo -n "Enter DATABASE_URL: "
        read DATABASE_URL
        echo -n "$DATABASE_URL" | gcloud secrets create parallaxmind-db-url --data-file=-
    fi
    
    if ! gcloud secrets describe vertex-project-id --quiet; then
        echo -n "$PROJECT_ID" | gcloud secrets create vertex-project-id --data-file=-
    fi
    
    echo -e "${GREEN}✅ Secrets created successfully!${NC}"
}

# Build and deploy
build_and_deploy() {
    echo -e "${YELLOW}🏗️  Building and deploying application...${NC}"
    
    # Trigger Cloud Build
    gcloud builds submit --config cloudbuild.yaml \
        --substitutions=_ENVIRONMENT=$ENVIRONMENT
    
    echo -e "${GREEN}✅ Build and deployment complete!${NC}"
}

# Configure ADK
configure_adk() {
    echo -e "${YELLOW}🤖 Configuring ADK agents...${NC}"
    
    # Initialize ADK
    adk init parallaxmind --project=$PROJECT_ID --region=$REGION
    adk config set project_id $PROJECT_ID
    adk config set region $REGION
    
    # Deploy agent configuration
    adk deploy --config=adk.yaml
    
    echo -e "${GREEN}✅ ADK configuration complete!${NC}"
}

# Verify deployment
verify_deployment() {
    echo -e "${YELLOW}🔍 Verifying deployment...${NC}"
    
    # Get service URLs
    BACKEND_URL=$(gcloud run services list --filter="metadata.name:parallaxmind-backend" --format="value(status.url)")
    FRONTEND_URL=$(gcloud run services list --filter="metadata.name:parallaxmind-frontend" --format="value(status.url)")
    
    echo -e "${GREEN}✅ Deployment verification complete!${NC}"
    echo -e "${BLUE}🌐 Backend URL: $BACKEND_URL${NC}"
    echo -e "${BLUE}🌐 Frontend URL: $FRONTEND_URL${NC}"
}

# Main deployment process
main() {
    echo -e "${BLUE}Starting deployment for project: $PROJECT_ID${NC}"
    echo -e "${BLUE}Region: $REGION${NC}"
    echo -e "${BLUE}Environment: $ENVIRONMENT${NC}"
    echo
    
    check_prerequisites
    setup_project
    create_secrets
    build_and_deploy
    configure_adk
    verify_deployment
    
    echo
    echo -e "${GREEN}🎉 ParallaxMind ADK System deployed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${BLUE}Your multi-agent research assistant is now live!${NC}"
}

# Handle script arguments
case "${1:-}" in
    "help" | "-h" | "--help")
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  help     Show this help message"
        echo "  check    Run prerequisites check only"
        echo "  setup    Setup project only"
        echo "  build    Build and deploy only"
        echo "  adk      Configure ADK only"
        echo "  verify   Verify deployment only"
        echo
        echo "Environment variables:"
        echo "  PROJECT_ID   - Google Cloud project ID"
        echo "  REGION       - Deployment region (default: us-central1)"
        echo "  ENVIRONMENT  - Environment name (default: production)"
        ;;
    "check")
        check_prerequisites
        ;;
    "setup")
        setup_project
        ;;
    "build")
        build_and_deploy
        ;;
    "adk")
        configure_adk
        ;;
    "verify")
        verify_deployment
        ;;
    *)
        main
        ;;
esac