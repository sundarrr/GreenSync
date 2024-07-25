# Import the smtplib module to handle sending emails
import smtplib

# Import MIMEText to create MIME objects
from email.mime.text import MIMEText

# Import traceback to handle exceptions and print error tracebacks
import traceback

# Define a function to send an email
def send_email(recipient_email, subject, message):
    try:
        # Create the HTML body of the email with the provided message
        body = f"""
    <html>
<body style="
display: flex;
align-items: center;
justify-content: center;">
<div class="container" style="background: #fff;
padding: 35px 65px;
border-radius: 12px;
text-align: -webkit-center;
row-gap: 20px;
box-shadow: 0 5px 10px rgba(0, 0, 0, 0.1);">
<header style=" height: 75px;text-align: -webkit-center;color: #fff;">
<img style=" height: 75px;"
src="https://media.licdn.com/dms/image/D560BAQHObNJRmUcxDw/company-logo_200_200/0/1719256775362/kerigreen_logo?e=1729123200&v=beta&t=S_xHM_d--9krewK_l-EigIMu-FANeRPhYKtjRUsOyeg"/>
</header>
<h4>{message}</h4>
</div>
</body>
</html>
    """
        # Create a MIMEText object with the HTML body
        html_message = MIMEText(body, 'html')

        # Set the email subject
        html_message['Subject'] = subject

        # Print statements for debugging purposes (commented out)
        # print("subject")
        # print(subject)
        # print(recipient_email)
        # print(html_message.as_string())

        # Set the sender email address
        html_message['From'] = "bcstechnologies.in@gmail.com"

        # Set the recipient email address
        html_message['To'] = recipient_email

        # Use smtplib to send the email via Gmail's SMTP server with SSL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            # Log in to the SMTP server using the sender's email credentials
            server.login("bcstechnologies.in@gmail.com", "zltsqeimgeimdgue")

            # Send the email from the sender to the recipient
            server.sendmail("bcstechnologies.in@gmail.com", recipient_email, html_message.as_string())
    except Exception as e:
        # Print the traceback of the exception if any error occurs
        print(traceback.format_exc())
