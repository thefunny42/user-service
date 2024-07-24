package userservice

import rego.v1

default allow := false

allow if {
	input.method == "GET"
	input.path == ["api", "users"]
}

allow if {
	some id in input.path
	input.method == "GET"
	input.path == ["api", "users", id]
}

allow if {
	some id in input.path
	some role in input.roles
	input.method == "DELETE"
	input.path == ["api", "users", id]
	role == "admin"
}

allow if {
	some role in input.roles
	input.method == "POST"
	input.path == ["api", "users"]
	role == "admin"
}
