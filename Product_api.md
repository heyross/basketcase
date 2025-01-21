# Products API Documentation

openapi: 3.0.0
info:
  title: Products API
  version: 1.2.4
  description: The Products API allows you to search the Kroger product catalog.
  contact:
    email: APISupport@kroger.com
  url: https://developer.kroger.com

servers:
  - url: https://api.kroger.com/v1

rate-limit:
  description: Public Products API rate limit
  daily-limit: 10000
  notes: >
    Rate limit is enforced by the number of calls to the endpoint,
    not individual API operations.

pagination:
  default-limit: 10
  parameters:
    - filter.limit: Sets a limit on the number of products returned
    - filter.start: Sets a number of results to skip in the response
  note: Search results order may vary between requests due to fuzzy search

paths:
  /products:
    get:
      summary: Product search
      description: Find products by search term or product Id
      parameters:
        - name: filter.term
          in: query
          description: Search term (3+ characters, max 8 words)
          example: milk
          schema:
            type: string
            minLength: 3
        - name: filter.locationId
          in: query
          description: Location ID (8 characters)
          example: "01400943"
          schema:
            type: string
            length: 8
        - name: filter.productId
          in: query
          description: Product ID (13 digits, comma-separated for multiple)
          example: "0001111060903"
          schema:
            type: string
            length: 13
        - name: filter.brand
          in: query
          description: Brand name (case-sensitive, pipe-separated)
          example: Kroger
        - name: filter.fulfillment
          in: query
          description: Fulfillment types (comma-separated)
          schema:
            type: string
            enum: [ais, csp, dth, sth]
        - name: filter.start
          in: query
          description: Number of products to skip
          schema:
            type: integer
            minimum: 1
            maximum: 250
        - name: filter.limit
          in: query
          description: Number of products to return
          schema:
            type: integer
            minimum: 1
            maximum: 50
      responses:
        '200':
          description: OK
        '400':
          description: Bad Request
        '401':
          description: Unauthorized
        '403':
          description: Forbidden
        '500':
          description: Internal Server Error

  /products/{id}:
    get:
      summary: Product details
      description: Get details for a specific product using 13-digit productId
      parameters:
        - name: id
          in: path
          required: true
          description: Product ID or UPC
          schema:
            type: string
        - name: filter.locationId
          in: query
          description: Location ID for price, availability, and aisle location
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
        '403':
          description: Forbidden
        '500':
          description: Internal Server Error

components:
  securitySchemes:
    ClientContext:
      type: oauth2
      flows:
        clientCredentials:
          tokenUrl: /connect/oauth2/token

additional-features:
  price:
    description: Available when locationId is provided
    objects:
      - price: Regular and promo price
      - nationalPrice: National regular and promo price
    note: Seasonal products return price only when available

  fulfillment-types:
    description: Available when locationId is provided
    types:
      instore: Sold in store at location
      shiptohome: Available for shipping
      delivery: Available for delivery
      curbside: Available for curbside pickup
    note: Instore indicates item is sold, not necessarily in stock

  inventory:
    description: Stock level indicator when available
    levels:
      - HIGH: Stock level is high
      - LOW: Stock level is low
      - TEMPORARILY_OUT_OF_STOCK: Item temporarily unavailable