# Locations API Documentation

openapi: 3.0.0
info:
  title: Locations API
  version: 1.2.2
  description: The Locations API provides access to all locations, chains, and departments owned by The Kroger Co.
  contact:
    email: APISupport@kroger.com
  url: https://developer.kroger.com

servers:
  - url: https://api.kroger.com/v1

rate-limit:
  description: Public Locations API rate limit
  daily-limit-per-endpoint: 1600
  note: Each endpoint has its own 1,600 call per day limit

pagination:
  supported: false
  default-limit: 10
  max-limit: 200
  note: >
    Default mile radius is 10 miles. When extending results with filter.limit,
    you may need to extend filter.radiusInMiles to get correct number of results.

paths:
  /locations:
    get:
      summary: Location list
      description: Returns a list of locations matching given criteria
      parameters:
        - name: filter.zipCode.near
          in: query
          description: Zip code starting point
          example: "45044"
          schema:
            type: string
        - name: filter.latLong.near
          in: query
          description: Latitude and longitude starting point
          example: "39.306346,-84.278902"
          schema:
            type: string
        - name: filter.lat.near
          in: query
          description: Latitude starting point
          example: "39.306346"
          schema:
            type: string
        - name: filter.lon.near
          in: query
          description: Longitude starting point
          example: "-84.278902"
          schema:
            type: string
        - name: filter.radiusInMiles
          in: query
          description: Mile radius for results
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 10
        - name: filter.limit
          in: query
          description: Number of results to return
          schema:
            type: integer
            minimum: 1
            maximum: 200
            default: 10
        - name: filter.chain
          in: query
          description: Chain name filter
          example: Kroger
        - name: filter.department
          in: query
          description: Department ID filter (comma-separated)
          example: "13"
          schema:
            type: string
            length: 2
        - name: filter.locationId
          in: query
          description: Location IDs (comma-separated)
          example: "01400390"
          schema:
            type: string
            length: 8
      responses:
        '200':
          description: OK
        '400':
          description: Bad Request
        '401':
          description: Unauthorized
        '404':
          description: Not Found
        '500':
          description: Internal Server Error

  /locations/{locationId}:
    get:
      summary: Location details
      description: Get details for a specific location
      parameters:
        - name: locationId
          in: path
          required: true
          description: Location ID
          example: "01400943"
          schema:
            type: string
            length: 8
      responses:
        '200':
          description: OK
        '400':
          description: Bad Request
        '401':
          description: Unauthorized
        '404':
          description: Not Found
        '500':
          description: Internal Server Error

    head:
      summary: Location query
      description: Determine if location exists
      parameters:
        - name: locationId
          in: path
          required: true
          description: Location ID
          example: "01400943"
          schema:
            type: string
            length: 8
      responses:
        '204':
          description: No Content
        '400':
          description: Incorrect locationId format
        '401':
          description: Unauthorized
        '404':
          description: Not Found
        '500':
          description: Internal Server Error

  /chains:
    get:
      summary: Chain list
      description: Get list of all chains owned by The Kroger Co.
      responses:
        '200':
          description: OK
        '401':
          description: Unauthorized
        '500':
          description: Internal Server Error

  /chains/{name}:
    get:
      summary: Chain details
      description: Get details for a specific chain
      parameters:
        - name: name
          in: path
          required: true
          description: Chain name
          example: Kroger
          schema:
            type: string
      responses:
        '200':
          description: OK
        '401':
          description: Unauthorized
        '404':
          description: Not Found
        '500':
          description: Internal Server Error

    head:
      summary: Chain query
      description: Determine if chain exists
      parameters:
        - name: name
          in: path
          required: true
          description: Chain name
          example: Kroger
          schema:
            type: string
      responses:
        '204':
          description: No Content
        '401':
          description: Unauthorized
        '404':
          description: Not Found
        '500':
          description: Internal Server Error

  /departments:
    get:
      summary: Department list
      description: Get list of all departments
      responses:
        '200':
          description: OK
        '400':
          description: Bad Request
        '401':
          description: Unauthorized
        '500':
          description: Internal Server Error

  /departments/{id}:
    get:
      summary: Department details
      description: Get details for a specific department
      parameters:
        - name: id
          in: path
          required: true
          description: Department ID
          example: "13"
          schema:
            type: string
            length: 2
      responses:
        '200':
          description: OK
        '400':
          description: Bad Request
        '401':
          description: Unauthorized
        '404':
          description: Not Found
        '500':
          description: Internal Server Error

    head:
      summary: Department query
      description: Determine if department exists
      parameters:
        - name: id
          in: path
          required: true
          description: Department ID
          example: "13"
          schema:
            type: string
            length: 2
      responses:
        '204':
          description: No Content
        '400':
          description: Bad Request
        '401':
          description: Unauthorized
        '404':
          description: Not Found
        '500':
          description: Internal Server Error

components:
  securitySchemes:
    ClientContext:
      type: oauth2
      flows:
        clientCredentials:
          tokenUrl: /connect/oauth2/token