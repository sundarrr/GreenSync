# IAT Group 4 (Section 3)
Team Members: Saravanan, Sundar, Rakul, Riya

# Checkout our website
<h2><a href="https://ecogreenmart.in">
https://ecogreenmart.in
</a></h2>
<h3>Deployed in Digital Ocean</h3>
<h3>Linux, Ubuntu, 1GB Ram Server</h3>

# Dashboard
![Community Page](Dashboard1.gif)
![Community Page](Dashboard2.gif)

# Cart
![Community Page](cart1.gif)

# Autosuggest
![Community Page](autosuggest.gif)

# Community
![Community Page](community.gif)

# Profiles and Orders
![Community Page](profileandorders.gif)

# Payment Success
![Community Page](paymentsuccess.gif)

# Events
![Community Page](events.gif)

# Admin Portal

# Orders Admin
![Community Page](ordersadmin.gif)

# Event List
![Community Page](eventlistadmin.gif)

# Products Admin
![Community Page](productsadmin.gif)



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
