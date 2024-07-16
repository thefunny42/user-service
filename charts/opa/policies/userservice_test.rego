package userservice_test

import rego.v1

import data.userservice

test_get_users if {
	userservice.allow with input as {"method": "GET", "path": ["api", "users"], "roles": []}
}

test_get_users_admin if {
	userservice.allow with input as {"method": "GET", "path": ["api", "users"], "roles": ["admin"]}
}

test_get_users_other if {
	userservice.allow with input as {"method": "GET", "path": ["api", "users"], "roles": ["other"]}
}

test_get_user if {
	userservice.allow with input as {"method": "GET", "path": ["api", "users", "0"], "roles": []}
}

test_get_user_admin if {
	userservice.allow with input as {"method": "GET", "path": ["api", "users", "0"], "roles": ["admin"]}
}

test_get_user_other if {
	userservice.allow with input as {"method": "GET", "path": ["api", "users", "0"], "roles": ["other"]}
}

test_delete_user if {
	not userservice.allow with input as {"method": "DELETE", "path": ["api", "users", "0"], "roles": []}
}

test_delete_user_admin if {
	userservice.allow with input as {"method": "DELETE", "path": ["api", "users", "0"], "roles": ["admin"]}
}

test_delete_user_other if {
	not userservice.allow with input as {"method": "DELETE", "path": ["api", "users", "0"], "roles": ["other"]}
}

test_post_user if {
	not userservice.allow with input as {"method": "POST", "path": ["api", "users"], "roles": []}
}

test_post_user_admin if {
	userservice.allow with input as {"method": "POST", "path": ["api", "users"], "roles": ["admin"]}
}

test_post_user_other if {
	not userservice.allow with input as {"method": "POST", "path": ["api", "users"], "roles": ["other"]}
}
