# Kroger API Documentation

## API Environments

Kroger provides two environments for API access:

| Environment    | Base URL                    | Purpose                                |
|---------------|----------------------------|----------------------------------------|
| Production    | `https://api.kroger.com/v1` | Live environment for production traffic |
| Certification | `https://api-ce.kroger.com/v1` | Testing environment (incomplete data)  |

### Important Notes

- **Production Environment**
  - Use for all production traffic
  - Required for Identity and Cart APIs testing
  - Supports real user accounts
  - Always use this environment when deploying for customer use

- **Certification Environment**
  - Use for testing API integrations
  - Data may be incomplete or inaccurate
  - User accounts are not available
  - Not suitable for Identity or Cart API testing

## Authentication

### OAuth2 Authentication

The API uses OAuth 2.0 for authentication. For server-to-server applications, use the Client Credentials flow:

```bash
POST https://api.kroger.com/v1/connect/oauth2/token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {base64(client_id:client_secret)}

grant_type=client_credentials&scope=product.compact
```

### Available Scopes

- `product.compact`: Read-only access to product data

### Token Response

```json
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "scope": "product.compact"
}
```

## Error Handling

The API returns two types of error responses:

### 1. Authentication Errors

Returned when there are issues with authentication or authorization:

```json
{
  "error": "invalid_token",
  "error_description": "The access token is invalid or has expired"
}
```

| Field | Type | Description |
|-------|------|-------------|
| error | string | Brief error description |
| error_description | string | Detailed error message |

### 2. API Errors

Returned for other API request issues:

```json
{
  "errors": {
    "timestamp": 1568391692365,
    "code": "PRODUCT-2011-400",
    "reason": "Field 'locationId' must have a length of 8 characters"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| timestamp | number | Error occurrence time (Unix timestamp) |
| code | string | Server error code (Format: API-ID-STATUS) |
| reason | string | Human-readable error description |

## Rate Limits

- Each endpoint has its own rate limit
- Limits are tracked per application (client ID)
- Rate limit information is included in response headers

## Best Practices

1. **Error Handling**
   - Always check for error responses
   - Implement proper retry logic with exponential backoff
   - Log detailed error information for debugging

2. **Authentication**
   - Cache access tokens until they expire
   - Refresh tokens before they expire to prevent service interruption
   - Never expose client secrets in client-side code

3. **Performance**
   - Use appropriate filter parameters to limit response size
   - Implement caching where appropriate
   - Batch requests when possible to reduce API calls

4. **Data Validation**
   - Validate location IDs are exactly 8 characters
   - Ensure search terms are at least 3 characters
   - Check response data before processing

## Testing

1. Start development using the Certification environment
2. Test thoroughly with error cases and edge conditions
3. Move to Production environment for final testing
4. Use real user accounts for Identity and Cart API testing
5. Monitor API response times and error rates

## Support

For API support:
- Email: APISupport@kroger.com
- Developer Portal: https://developer.kroger.com