# Example Code Review

## Code Reviewed
```python
def get_user(id):
    query = f"SELECT * FROM users WHERE id = {id}"
    return db.execute(query)
```

## Summary
This function has a critical SQL injection vulnerability and lacks proper documentation and type hints.

## Critical Issues
- **SQL Injection**: Using f-strings to build SQL queries allows attackers to inject malicious SQL. Use parameterized queries instead.

## Improvements
- Add type hints for the parameter and return value
- Add a docstring explaining the function's purpose
- Use parameterized queries or an ORM
- Consider returning a typed User object instead of raw query results

## Good Practices Observed
- Function has a clear, single responsibility
- Function name is descriptive

## Suggested Fix
```python
def get_user(user_id: int) -> User | None:
    """Retrieve a user by their ID.

    Args:
        user_id: The unique identifier of the user.

    Returns:
        User object if found, None otherwise.
    """
    return db.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
```
