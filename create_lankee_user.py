
from getpass import getpass

from src.core.database import Database
from src.repositories import UserRepository, RoleRepository
from src.services.user_management_service import UserManagementService


def main():

    database = Database()
    database.initialize()

    user_repository = UserRepository(database)
    role_repository = RoleRepository(database)

    service = UserManagementService(
        user_repository,
        role_repository,
        database
    )

    username = "lankee"
    full_name = "Thompson LanKee"

    # Check whether the username already exists
    existing_user = user_repository.get_by_username(username)

    if existing_user:
        print(f"User '{username}' already exists.")
        return

    # Retrieve every existing role
    roles = service.get_roles()

    if not roles:
        print("No roles found. Create roles before creating this user.")
        return

    role_ids = [role.role_id for role in roles]

    print("The following roles will be assigned:")
    for role in roles:
        print(f"- {role.role_name}")

    password = getpass("Enter the new account password: ")

    service.create_user(
        username=username,
        full_name=full_name,
        password=password,
        role_ids=role_ids
    )

    print("\nUser created successfully!")
    print(f"Username: {username}")
    print(f"Full name: {full_name}")
    print(f"Assigned roles: {len(role_ids)}")


if __name__ == "__main__":
    main()
