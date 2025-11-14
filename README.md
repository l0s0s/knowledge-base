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

- **API Root**: http://localhost:8000/knowledge/
- **API Endpoints**: Open any API endpoint in browser (e.g., http://localhost:8000/knowledge/) to see interactive documentation
- **Admin Panel**: http://localhost:8000/knowledge/admin/
- **Swagger Documentation**: http://localhost:8000/knowledge/docs/
- **ReDoc Documentation**: http://localhost:8000/knowledge/redoc/
- **Static Files** (CSS, JS for admin/docs): http://localhost:8000/knowledge/static/
- **Media Files** (uploaded content): http://localhost:8000/knowledge/media/
 

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

## API Endpoints - Detailed Documentation

Base URL: `http://localhost:8000/knowledge/`

### Knowledge Endpoints

#### 1. List Knowledge Entries

**Endpoint:** `GET /knowledge/`

**Description:** Retrieve a paginated list of knowledge entries. Supports filtering and ordering.

**Query Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `user_id` | string | Filter by exact user ID | `user_id=user123` |
| `text__icontains` | string | Filter by text content (contains, case-insensitive) | `text__icontains=python` |
| `created_at__gte` | datetime | Filter by creation date (greater than or equal) | `created_at__gte=2024-01-01T00:00:00Z` |
| `created_at__lte` | datetime | Filter by creation date (less than or equal) | `created_at__lte=2024-12-31T23:59:59Z` |
| `updated_at__gte` | datetime | Filter by update date (greater than or equal) | `updated_at__gte=2024-01-01T00:00:00Z` |
| `updated_at__lte` | datetime | Filter by update date (less than or equal) | `updated_at__lte=2024-12-31T23:59:59Z` |
| `ordering` | string | Order by field. Prefix with `-` for descending | `ordering=-created_at` or `ordering=user_id` |
| `page` | integer | Page number for pagination (default: 1) | `page=2` |
| `page_size` | integer | Number of items per page (default: 20, max: 100) | `page_size=50` |

**Available ordering fields:** `created_at`, `updated_at`, `user_id`

**Example Request:**
```bash
GET /knowledge/?user_id=user123&text__icontains=python&ordering=-created_at&page=1&page_size=20
```

**Response (200 OK):**
```json
{
  "count": 100,
  "next": "http://localhost:8000/knowledge/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "user_id": "user123",
      "text": "Python is a programming language",
      "quiz": ["question1", "question2"],
      "images": [
        {
          "id": 1,
          "image": "http://localhost:8000/knowledge/media/knowledge_images/image1.png",
          "created_at": "2024-01-15T10:30:00Z"
        }
      ],
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

**Pagination:**
- Default page size: 20 items
- Max page size: 100 items
- Use `page_size` parameter to customize number of items per page
- `count`: Total number of items
- `next`: URL to next page (null if last page)
- `previous`: URL to previous page (null if first page)
- `results`: Array of knowledge entries

---

#### 2. Get Single Knowledge Entry

**Endpoint:** `GET /knowledge/{id}/`

**Description:** Retrieve a single knowledge entry by ID.

**Path Parameters:**
- `id` (integer, required): Knowledge entry ID

**Example Request:**
```bash
GET /knowledge/1/
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": "user123",
  "text": "Python is a programming language",
  "quiz": ["question1", "question2"],
  "images": [
    {
      "id": 1,
      "image": "http://localhost:8000/knowledge/media/knowledge_images/image1.png",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "image": "http://localhost:8000/knowledge/media/knowledge_images/image2.jpg",
      "created_at": "2024-01-15T11:00:00Z"
    }
  ],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Not found."
}
```

---

#### 3. Create Knowledge Entry

**Endpoint:** `POST /knowledge/`

**Description:** Create a new knowledge entry.

**Request Body:**
```json
{
  "user_id": "string (required, max 255 chars)",
  "text": "string (required)",
  "quiz": ["array", "of", "strings"] // optional, must be array, default: []
}
```

**Example Request:**
```bash
POST /knowledge/
Content-Type: application/json

{
  "user_id": "user123",
  "text": "Django is a web framework for Python",
  "quiz": ["What is Django?", "What is REST API?"]
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": "user123",
  "text": "Django is a web framework for Python",
  "quiz": ["What is Django?", "What is REST API?"],
  "images": [],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

**Response (400 Bad Request) - Validation Error:**
```json
{
  "quiz": ["Quiz must be a list."]
}
```

---

#### 4. Update Knowledge Entry

**Endpoint:** `PATCH /knowledge/{id}/` (partial update)
**Endpoint:** `PUT /knowledge/{id}/` (full update)

**Description:** Update an existing knowledge entry. Note: `user_id` cannot be updated, only `text` and `quiz` can be modified.

**Path Parameters:**
- `id` (integer, required): Knowledge entry ID

**Request Body (PATCH - partial):**
```json
{
  "text": "string (optional)",
  "quiz": ["array"] // optional, must be array
}
```

**Request Body (PUT - full):**
```json
{
  "text": "string (required)",
  "quiz": ["array"] // required, must be array
}
```

**Example Request:**
```bash
PATCH /knowledge/1/
Content-Type: application/json

{
  "text": "Updated text content",
  "quiz": ["new question 1", "new question 2"]
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": "user123",
  "text": "Updated text content",
  "quiz": ["new question 1", "new question 2"],
  "images": [...],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T11:30:00Z"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Not found."
}
```

---

#### 5. Delete Knowledge Entry (Soft Delete)

**Endpoint:** `DELETE /knowledge/{id}/`

**Description:** Soft delete a knowledge entry. The entry is not permanently deleted but marked as deleted. It will not appear in list requests but can be restored.

**Path Parameters:**
- `id` (integer, required): Knowledge entry ID

**Example Request:**
```bash
DELETE /knowledge/1/
```

**Response (204 No Content):**
No response body

**Response (404 Not Found):**
```json
{
  "detail": "Not found."
}
```

**Note:** After soft delete, the entry will not appear in `GET /knowledge/` list, but can be restored using the restore endpoint.

---

#### 6. Restore Deleted Entry

**Endpoint:** `POST /knowledge/{id}/restore/`

**Description:** Restore a soft-deleted knowledge entry.

**Path Parameters:**
- `id` (integer, required): Knowledge entry ID

**Example Request:**
```bash
POST /knowledge/1/restore/
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": "user123",
  "text": "Restored content",
  "quiz": [],
  "images": [],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "Knowledge entry is not deleted."
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Knowledge entry not found."
}
```

---

#### 7. Upload Image

**Endpoint:** `POST /knowledge/{id}/upload-image/`

**Description:** Upload an image file to associate with a knowledge entry.

**Path Parameters:**
- `id` (integer, required): Knowledge entry ID

**Request:**
- Content-Type: `multipart/form-data`
- Form field: `image` (file, required)

**Example Request:**
```bash
POST /knowledge/1/upload-image/
Content-Type: multipart/form-data

image: [binary file data]
```

**Using cURL:**
```bash
curl -X POST http://localhost:8000/knowledge/1/upload-image/ \
  -F "image=@/path/to/image.jpg"
```

**Using JavaScript (FormData):**
```javascript
const formData = new FormData();
formData.append('image', fileInput.files[0]);

fetch('http://localhost:8000/knowledge/1/upload-image/', {
  method: 'POST',
  body: formData
});
```

**Response (201 Created):**
```json
{
  "id": 5,
  "image": "http://localhost:8000/knowledge/media/knowledge_images/image_abc123.jpg",
  "created_at": "2024-01-15T12:00:00Z"
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "Image file is required."
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Not found."
}
```

---

#### 8. Delete Image

**Endpoint:** `DELETE /knowledge/{id}/images/{image_id}/`

**Description:** Delete a specific image associated with a knowledge entry.

**Path Parameters:**
- `id` (integer, required): Knowledge entry ID
- `image_id` (integer, required): Image ID to delete

**Example Request:**
```bash
DELETE /knowledge/1/images/5/
```

**Response (204 No Content):**
No response body

**Response (404 Not Found):**
```json
{
  "detail": "Image not found."
}
```

---

### Response Field Descriptions

#### Knowledge Object
| Field | Type | Description | Read-only |
|-------|------|-------------|-----------|
| `id` | integer | Primary key | Yes |
| `user_id` | string | User identifier (max 255 chars) | No (cannot be updated) |
| `text` | string | Text content | No |
| `quiz` | array | Array of quiz items (strings) | No |
| `images` | array | Array of image objects | Yes |
| `created_at` | datetime | Creation timestamp (ISO 8601) | Yes |
| `updated_at` | datetime | Last update timestamp (ISO 8601) | Yes |

#### Image Object
| Field | Type | Description | Read-only |
|-------|------|-------------|-----------|
| `id` | integer | Primary key | Yes |
| `image` | string | Full URL to image file | Yes |
| `created_at` | datetime | Creation timestamp (ISO 8601) | Yes |

### Error Responses

All endpoints may return the following error responses:

**400 Bad Request:**
```json
{
  "field_name": ["Error message"],
  "detail": "Error message"
}
```

**404 Not Found:**
```json
{
  "detail": "Not found."
}
```

**500 Internal Server Error:**
```json
{
  "detail": "A server error occurred."
}
```

### Filtering Examples

**Filter by user ID:**
```
GET /knowledge/?user_id=user123
```

**Filter by text containing "python":**
```
GET /knowledge/?text__icontains=python
```

**Filter by date range:**
```
GET /knowledge/?created_at__gte=2024-01-01T00:00:00Z&created_at__lte=2024-12-31T23:59:59Z
```

**Combine filters:**
```
GET /knowledge/?user_id=user123&text__icontains=django&ordering=-created_at
```

**Pagination with custom page size:**
```
GET /knowledge/?page=2&page_size=50
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

### Testing Deployed Application

To test a deployed application at a specific URL, use the deployment test script:

```bash
python test_deployed.py <BASE_URL>
```

**Example:**
```bash
# Test local deployment
python test_deployed.py http://localhost:8000

# Test production deployment
python test_deployed.py https://api.example.com
```

**Requirements:**
```bash
pip install requests Pillow
```

The script tests:
- All API endpoints (CRUD operations)
- Soft delete and restore functionality
- Image upload and deletion
- Filtering, pagination, and sorting
- Data validation
- Error handling (404, 400 responses)

The script provides colored output showing which tests passed or failed, and a summary at the end.

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

Access at: http://localhost:8000/knowledge/admin/

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

API documentation is automatically generated using OpenAPI/Swagger and is available at:

- **Swagger UI**: http://localhost:8000/knowledge/docs/
- **ReDoc**: http://localhost:8000/knowledge/redoc/
- **OpenAPI JSON**: http://localhost:8000/knowledge/openapi.json

The Swagger UI provides:
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