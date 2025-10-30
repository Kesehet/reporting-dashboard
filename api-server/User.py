class User:
    def __init__(self, email, password, role):
        self.email = email
        self.password = password
        self.role = role

    def __repr__(self):
        return f"<User {self.email}>"

