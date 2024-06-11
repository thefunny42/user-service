# User service

Simple user service with two endpoints:

1. `/api/users` with a `GET` to retrieve a list of users as a JSON, i.e:

        {"users":[{"name":"Arthur","email":"arthur@example.com"}]}

2. `/api/users` with a `POST` to create a user by providing a JSON in the body
    with:
    - `name` as a string, up to 256 characters,
    - `email` as a string and valid email, up to 256 characters.

    If the requirements are not meet the service with return an 422 error.

To use those endpoints you need to be authenticated with a Bearer token that
is a JWT token using `HS256` and the configured secret, with a property `roles`
that is an array. To create a user that array must contain at least `admin`.

The authorization is deletegated to [OPA](https://www.openpolicyagent.org/).

## Deployment

### Testing

## Configuration

The following configuration variables are available:

- `USER_SERVICE_KEY`: JWT key used to authenticate to the service.
- `USER_SERVICE_ISSUER`: Issuer expected in the JWT key used to authenticate.
- `USER_SERVICE_LOG`: Custom logging configuration (a default one is provided).
- `AUTHORIZATION_ENDPOINT`: URL to the OPA server.
- `AUTHORIZATION_POLICY`: Policy to use on the OPA server (default to userservice).


## Development

There is a dev container that can be used with vscode. It will take care of
starting an [OPA](https://www.openpolicyagent.org/) server in the background
to server the policies. [Hatch](https://hatch.pypa.io/latest/) is used as a
packaging tool, to run test and code analysis.

### Testing with curl

There is an helper script to generate a token with the configure key. First
start the service in a terminal:

    hatch run user-service

You can retrieve the list of users:

    MY_TOKEN=$(hatch run new-user-service-token)
    curl -H "Authorization: Bearer $MY_TOKEN" http://localhost:8000/api/users

You can add a user:

    MY_TOKEN=$(hatch run new-user-service-token admin)
    curl -H "Authorization: Bearer $MY_TOKEN" -H 'Content-Type: application/json' -X POST -d '{"name": "Arthur", "email": "arthur@example.com"}' http://localhost:8000/api/users
