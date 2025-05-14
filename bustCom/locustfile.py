from locust import HttpUser, task, between
from bs4 import BeautifulSoup
class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def index(self):
        self.client.get("/")


    @task
    def dashboard(self):
        self.client.get("/dashboard/")




    def on_start(self):
        response = self.client.get("/login/")
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.find("input", {"name": "csrfmiddlewaretoken"}).get("value")

        self.client.post(
            "/login/",
            {
                "username": "testuser",
                "password": "testpass",
                "csrfmiddlewaretoken": csrf_token,
            },
            headers={"Referer": self.client.base_url + "/login/"},
        )
