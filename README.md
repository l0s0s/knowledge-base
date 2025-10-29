# Knowledge Base API

Django REST Framework API for managing knowledge base entries with support for images, quizzes, and soft deletion.

## Features

- RESTful API with full CRUD operations
- Soft delete functionality with restore capability
- Image upload and management
- Comprehensive filtering and search
- Pagination support
- Admin interface for content management
- OpenAPI/Swagger documentation
- PostgreSQL database
- Docker-based deployment
- Comprehensive test coverage

## Quick Start

### One-command Deployment

Run the setup script:

```bash
./setup.sh
```

Or use Make:

```bash
make setup
```

This will:
- Set up environment variables
- Build Docker containers
- Start PostgreSQL and Django services
- Run migrations
- Collect static files

After setup, create a superuser to access the admin panel:

```bash
make create-superuser
```

Alternatively, using Docker Compose directly:

```bash
docker-compose up -d
```

### Access Points

- **API Root**: http://localhost:8000/api/
- **API Endpoints**: Open any API endpoint in browser (e.g., http://localhost:8000/api/knowledge/) to see interactive documentation
- **Admin Panel**: http://localhost:8000/admin/
 

Default admin credentials (if created by setup):
- Username: `admin`
- Email: `admin@example.com`
- Password: (you'll be prompted during setup)

## Project Structure

```
knowledge-base/
├── api/                    # Main application
│   ├── models.py          # Knowledge and KnowledgeImage models
│   ├── views.py           # API viewsets
│   ├── serializers.py     # DRF serializers
│   ├── filters.py         # Filtering logic
│   ├── admin.py           # Django admin configuration
│   ├── urls.py            # API routes
│   └── tests.py           # Test suite
├── knowledge_base/        # Django project settings
│   ├── settings.py        # Configuration
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py            # WSGI application
├── docker-compose.yml     # Docker services
├── Dockerfile             # Django container
├── requirements.txt       # Python dependencies
└── Makefile              # Common commands
```

## API Endpoints

### Knowledge Endpoints

#### List Knowledge Entries
```
GET /api/knowledge/
```

Query Parameters:
- `user_id`: Filter by exact user ID
- `user_id__icontains`: Filter by user ID (contains)
- `text__icontains`: Filter by text content (contains)
- `created_at__gte`: Filter by creation date (greater than or equal)
- `created_at__lte`: Filter by creation date (less than or equal)
- `updated_at__gte`: Filter by update date (greater than or equal)
- `updated_at__lte`: Filter by update date (less than or equal)
- `search`: Search in user_id and text fields
- `ordering`: Order by field (e.g., `created_at`, `-created_at`, `user_id`)
- `page`: Page number for pagination

Response includes pagination metadata.

#### Get Knowledge Entry
```
GET /api/knowledge/{id}/
```

#### Create Knowledge Entry
```
POST /api/knowledge/
```

Request Body:
```json
{
  "user_id": "string",
  "text": "string",
  "quiz": []
}
```

#### Update Knowledge Entry
```
PATCH /api/knowledge/{id}/
PUT /api/knowledge/{id}/
```

Request Body:
```json
{
  "text": "string",
  "quiz": []
}
```

#### Delete Knowledge Entry (Soft Delete)
```
DELETE /api/knowledge/{id}/
```

#### Restore Deleted Entry
```
POST /api/knowledge/{id}/restore/
```

#### Upload Image
```
POST /api/knowledge/{id}/upload-image/
```

Content-Type: `multipart/form-data`

Form Data:
- `image`: Image file

#### Delete Image
```
DELETE /api/knowledge/{id}/images/{image_id}/
```

## Testing

Run all tests with one command:

```bash
make test
```

Or locally (if you have Django setup):

```bash
make test-local
```

The test suite covers:
- CRUD operations
- Soft delete and restore
- Image upload and deletion
- Filtering and search
- Pagination
- Data validation

## Database Models

### Knowledge
- `id`: Primary key
- `user_id`: String field (indexed)
- `text`: Text content
- `quiz`: JSON field (array)
- `created_at`: Creation timestamp
- `updated_at`: Update timestamp
- `deleted_at`: Soft delete timestamp (nullable)

### KnowledgeImage
- `id`: Primary key
- `knowledge`: Foreign key to Knowledge
- `image`: Image file
- `created_at`: Creation timestamp

## Admin Interface

The Django admin interface allows you to:
- Create, edit, and delete knowledge entries
- Upload and manage images inline
- View all entries with filtering options
- Restore soft-deleted entries
- Browse entry history

Access at: http://localhost:8000/admin/

## Development

### Local Development Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
```

3. Update `.env` with your database credentials

4. Run migrations:
```bash
python manage.py migrate
```

5. Create superuser:
```bash
python manage.py createsuperuser
```

6. Run development server:
```bash
python manage.py runserver
```

### Common Commands

```bash
make up              # Start services
make down            # Stop services
make build           # Rebuild containers
make migrate         # Run migrations
make makemigrations  # Create migrations
make shell           # Django shell
make logs            # View logs
make test            # Run tests
```

## Environment Variables

Create a `.env` file with:

```env
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=knowledge_base
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

## API Documentation

API documentation is automatically generated and available on each endpoint page when accessed through a browser. Simply open any API endpoint (e.g., `http://localhost:8000/api/knowledge/`) in your browser to see:

- Interactive documentation with examples
- Available HTTP methods (GET, POST, PATCH, DELETE)
- Request/response schemas
- All query parameters and filters
- Form for testing API calls directly in the browser

The documentation includes:
- All available endpoints with detailed descriptions
- Request/response schemas with field types
- Filtering and pagination options
- Example requests and responses

## Production Considerations

Before deploying to production:

1. Change `SECRET_KEY` in `.env`
2. Set `DEBUG=False`
3. Configure proper `ALLOWED_HOSTS`
4. Set up proper database credentials
5. Configure static file serving (e.g., nginx)
6. Set up media file storage (e.g., S3)
7. Enable HTTPS
8. Set up proper database backups

## License

This project is provided as-is for development purposes.