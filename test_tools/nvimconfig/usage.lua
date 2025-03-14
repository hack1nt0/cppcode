local sqlite = require("sqlite")

-- open and close a database
local db = sqlite.open("test.db") -- or ":memory:"
-- db:close()

-- execute commands with db:exec         command   raw (don't parse as JSON)
local result = db:exec("SELECT sqlite_version();", false)

-- or with db:sql (appends ";", parses JSON)
local result = db:sql("SELECT sqlite_version()")

-- create a table
db:sql("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
-- or
db:execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL);")
-- or
db:create_table("users", {
    "id INTEGER PRIMARY KEY",
    "name TEXT NOT NULL",
})

-- insert a record
db:sql("INSERT INTO users (id, name) VALUES (1, 'John Doe')")
-- or
db:insert("users", { id = 1, name = "John Doe" })

-- fetch records
local users = db:sql("SELECT * FROM users WHERE name = 'John Doe'")
-- or
local users = db:select("users", "name = 'John Doe'", "*")

-- update a record
db:sql("UPDATE users SET name = 'Jane Doe' WHERE id = 1")
-- or
db:update("users", "id = 1", { name = "Jane Doe" })

-- delete a record
db:sql("DELETE FROM users WHERE id = 1")
-- or
db:delete("users", "id = 1")

-- drop a table
db:sql("DROP TABLE users")
-- or
db:drop_table("users")

-- get tables and columns
local tables = db:get_tables()
local columns = db:get_columns("users")
