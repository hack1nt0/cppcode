-- PRAGMA foreign_keys = ON;
------------
BEGIN;
create table if not exists task (
    id INTEGER PRIMARY KEY,
    `group` TEXT,
    name TEXT NOT NULL COLLATE NOCASE,
    dat TEXT NOT NULL,
    sol TEXT,
    gen TEXT,
    cmp TEXT,
    chk TEXT,
    ctime INT NOT NULL,
    mtime INT NOT NULL,
    solved INT ---0: untried, 1: solved, 2: unsolved
);

-- drop table if exists task2;
create table if not exists task2 (
    id INTEGER PRIMARY KEY,
    fullname TEXT NOT NULL COLLATE NOCASE,
    dat BLOB NOT NULL,
    ctime INT NOT NULL,
    mtime INT NOT NULL,
    `status` INT ---0: untried, 1: solved, 2: unsolved, 3: marked
);

-- create table if not exists lang (
--     id INTEGER PRIMARY KEY,
--     suffix TEXT NOT NULL COLLATE NOCASE,
--     template TEXT,
--     build TEXT,
--     run TEXT,
--     UNIQUE(suffix)
-- );

-- create table if not exists taskindex (
--     id INTEGER PRIMARY KEY,
--     relpath TEXT,
--     `group` TEXT,
--     name TEXT NOT NULL COLLATE NOCASE,
--     cpulimit INT,
--     memlimit INT,
--     url TEXT,
--     interactive INT,
--     ctime INT NOT NULL,
--     mtime INT NOT NULL,
--     solved INT, ---0: untried, 1: solved, 2: unsolved
--     UNIQUE(relpath)
-- );


COMMIT;
