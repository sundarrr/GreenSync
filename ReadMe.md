# IAT Group 4 (Section 3)
Team Members: Saravanan, Sundar, Rakul, Riya

# Checkout our website
<a href="https://ecogreenmart.in">
https://ecogreenmart.in
</a>


# Loading and Dumping Data with Django Fixtures

This guide provides instructions on how to dump data from your Django application into a JSON file and how to load data from a JSON file into your Django application. This process is useful for backing up data, migrating data between environments, or loading initial data for your application.

## Dumping Data to a JSON File

To dump data from your Django application to a JSON file, you can use the `dumpdata` management command. This command allows you to export the data from the entire database or specific apps or models into a JSON format.

### Steps:

1. Open your terminal or command prompt.
2. Navigate to your Django project directory.
3. Run the following command to dump data from all applications:


python manage.py dumpdata > initial_data.json

python manage.py dumpdata userPortal > userPortal/fixtures/initial_data.json
python manage.py dumpdata adminPortal > adminPortal/fixtures/initial_data.json

python manage.py loaddata initial_data.json
