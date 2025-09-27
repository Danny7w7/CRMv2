# Health Insurance CRM

A robust and scalable **Customer Relationship Management (CRM)** platform designed for health insurance providers.  
This system enhances communication between agents and clients, streamlines policy management, and provides actionable insights for sales supervision and reporting.

---

## 🚀 Features

- **Bidirectional Text Messaging**  
  Seamless communication between agents and clients via SMS.

- **Integrated Dialer & Call Management**  
  Built-in dialer for handling inbound and outbound calls.

- **Third-Party API Integrations**  
  - [Telnyx](https://telnyx.com)  
  - [Twilio](https://www.twilio.com)  
  - [AWS](https://aws.amazon.com)  
  - [CMS Health Marketplace (USA)](https://www.healthcare.gov/marketplace/)

- **Real-Time Performance**  
  - WebSocket cache management  
  - Deployment with Daphne Channels for high concurrency  

- **User & Policy Management**  
  - User and role administration  
  - Policy tracking and monitoring  
  - Agent and supervisor reporting dashboards  

- **Productivity Tools**  
  - Custom alerts and notifications  
  - Integrated calendars and scheduling  
  - Modular design to create and assign features as services for other businesses  

---

## 🛠️ Tech Stack

- **Backend**: Python, Django, Django Channels, Daphne  
- **Real-Time Communication**: WebSockets  
- **Integrations**: Telnyx, Twilio, AWS, CMS Marketplace API  
- **Database**: MySQL 
- **Deployment**: Ubuntu 

---

## 📦 Installation (Basic Setup)

```bash
# Clone the repository
git clone https://github.com/Danny7w7/CRMv2.git
cd CRMv2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # (Linux/Mac)
venv\Scripts\activate     # (Windows)

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Start development server
python manage.py runserver
