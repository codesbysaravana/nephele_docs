from app.services.llm_service import generate_response


class InterviewAgent:

    def chat(self, user_text):

        response = generate_response(user_text)

        return response
