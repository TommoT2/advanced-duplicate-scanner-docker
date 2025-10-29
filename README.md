# 🔍 Advanced Duplicate Scanner

Enterprise-grade duplicate file detection with AI integration, cloud support, and MCP tools integration.

![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Python](https://img.shields.io/badge/Python-3.11-blue)

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- 8GB+ RAM available
- Windows 10/11 with WSL2 (for Windows)

### 1. Clone Repository
```bash
git clone https://github.com/TommoT2/advanced-duplicate-scanner-docker.git
cd advanced-duplicate-scanner-docker
```

### 2. Configure Environment
```bash
# Copy and edit environment file
cp .env.example .env.local

# Edit .env.local with your settings:
# - Set DATA_PATH to your Windows data directory
# - Change POSTGRES_PASSWORD to a secure password
# - Update SECRET_KEY for production
```

### 3. Deploy with Docker Compose
```bash
# Build and start all services
docker-compose --env-file .env.local up -d

# View logs (optional)
docker-compose logs -f
```

### 4. Access Application
- **Web UI**: http://localhost:3000
- **API Documentation**: http://localhost:3000/api/docs
- **Health Check**: http://localhost:3000/health

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web UI (FastAPI)                    │
│            http://localhost:3000                       │
└─────────────────┬───────────────────────────────────────┘
                  │ REST API + WebSocket
┌─────────────────▼───────────────────────────────────────┐
│              FastAPI Server                            │  
│         + MCP Tool Integration                          │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────┼─────────┐
        │         │         │
┌───────▼──┐ ┌────▼───┐ ┌───▼────────┐
│PostgreSQL│ │ Redis  │ │   Worker   │
│    DB    │ │ Cache  │ │  Process   │
└──────────┘ └────────┘ └────────────┘
```

## 🔧 Core Features

### 🔍 Advanced Scanning
- **BLAKE3 + xxHash64** for optimal performance
- **Chunked processing** for large files (resume support)
- **Multi-threaded** parallel processing
- **Memory efficient** streaming

### ☁️ Cloud Integration
- **OneDrive** via Microsoft Graph API
- **Dropbox** via API v2
- **Google Drive** via Drive API
- **rclone** for 40+ additional providers

### 🤖 AI-Powered Analysis
- **Semantic duplicate detection** beyond hashing
- **Context7 MCP integration** for intelligent suggestions
- **Perplexity API** for advanced pattern recognition
- **Smart categorization** and risk assessment

### 🛡️ Enterprise Security
- **Atomic operations** with rollback support
- **Audit logging** for all actions
- **Backup before deletion** policy
- **Container isolation** for security

## 📋 API Endpoints

### Health & Status
```http
GET /health                    # Basic health check
GET /api/health/detailed       # Detailed system status
```

### Scanner Operations
```http
GET  /api/v1/scanner/status    # Get scanner status
POST /api/v1/scanner/scan      # Start new scan
GET  /api/v1/scanner/sessions  # List scan sessions
```

### File Management
```http
GET    /api/v1/files/           # List processed files
GET    /api/v1/files/{id}       # Get file details
DELETE /api/v1/files/{id}       # Mark file for deletion
```

### Duplicate Management
```http
GET  /api/v1/duplicates/groups       # List duplicate groups
POST /api/v1/duplicates/groups/{id}/resolve  # Resolve duplicates
GET  /api/v1/duplicates/stats        # Get statistics
```

## 🔌 MCP Integration

This application integrates with Docker Desktop's MCP toolkit for enhanced functionality:

- **Filesystem MCP** (11 tools): Native file operations
- **Desktop Commander MCP** (25 tools): System integration
- **Docker MCP** (1 tool): Container management
- **Context7 MCP** (2 tools): AI-powered analysis
- **curl/Fetch MCP**: Cloud API integration

## 🗃️ Database Schema

### Core Tables
- `scan_sessions` - Scan configuration and progress
- `file_records` - Individual file metadata and hashes
- `duplicate_groups` - Groups of duplicate files
- `duplicate_memberships` - File membership in groups
- `cloud_connections` - Cloud service credentials

## 🛠️ Development

### Local Development Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up database
alembic upgrade head

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Code Quality
```bash
# Format code
black app/

# Lint code
ruff app/

# Type checking
mypy app/
```

## 🐳 Docker Operations

### View Service Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f duplicate-scanner
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart duplicate-scanner
```

### Database Operations
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U scanner -d duplicates

# Backup database
docker-compose exec postgres pg_dump -U scanner duplicates > backup.sql

# Restore database
docker-compose exec -T postgres psql -U scanner duplicates < backup.sql
```

### Scale Workers
```bash
# Scale worker processes
docker-compose up -d --scale scanner-worker=4
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_PATH` | `C:/Data` | Host path to scan |
| `POSTGRES_PASSWORD` | `scannerpass` | Database password |
| `SCANNER_WORKERS` | `4` | Number of worker threads |
| `SCANNER_CHUNK_SIZE` | `8388608` | Chunk size (8MB) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DEBUG` | `False` | Debug mode |
| `MCP_ENABLED` | `True` | Enable MCP integration |

### Performance Tuning

#### For High-Performance Systems
```env
SCANNER_WORKERS=8
SCANNER_CHUNK_SIZE=16777216  # 16MB chunks
WORKER_CONCURRENCY=8
```

#### For Memory-Constrained Systems
```env
SCANNER_WORKERS=2
SCANNER_CHUNK_SIZE=4194304   # 4MB chunks
WORKER_CONCURRENCY=2
```

## 🔒 Security Considerations

### Production Deployment
1. **Change all default passwords**
2. **Generate secure SECRET_KEY**
3. **Use HTTPS with SSL certificates**
4. **Configure firewall rules**
5. **Enable rate limiting**
6. **Set up log monitoring**

### Data Privacy
- Files are accessed read-only by default
- No file content is stored in database
- Only metadata and hashes are persisted
- Cloud credentials are encrypted at rest

## 📊 Monitoring & Observability

### Health Checks
- **Container health**: Built-in Docker health checks
- **Service health**: `/health` and `/api/health/detailed` endpoints
- **Database connectivity**: Automatic connection monitoring
- **Redis connectivity**: Cache availability monitoring

### Logging
- **Structured JSON logs** via structlog
- **Container logs** via Docker logging drivers
- **Application metrics** via Prometheus (optional)
- **Error tracking** with detailed stack traces

## 🚨 Troubleshooting

### Common Issues

#### Container won't start
```bash
# Check logs
docker-compose logs duplicate-scanner

# Check system resources
docker system df
docker system prune  # Clean up if needed
```

#### Database connection errors
```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres pg_isready -U scanner
```

#### Performance issues
- **Increase worker count** for more CPU cores
- **Increase chunk size** for faster I/O
- **Check disk space** and I/O performance
- **Monitor memory usage** with `docker stats`

### Support

For issues and questions:
1. Check the logs first: `docker-compose logs -f`
2. Verify configuration in `.env` file
3. Ensure Docker Desktop has sufficient resources
4. Check firewall and antivirus settings

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

**⚡ Ready to eliminate duplicate files? Start with `docker-compose up -d` and open http://localhost:3000!**