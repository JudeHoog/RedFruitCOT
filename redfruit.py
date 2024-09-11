import re
import logging
import boto3
from botocore.exceptions import ClientError
import time

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def generate_conversation(bedrock_client, model_id, system_prompts, messages, max_gen_len):
    """
    Sends messages to a model and returns the generated response.
    """
    logger.info(f"Generating message with model {model_id}")

    # Inference parameters
    temperature = 0.5
    top_p = 0.9
    max_tokens = max_gen_len  # Limit response to max_gen_len tokens

    inference_config = {"temperature": temperature, "maxTokens": max_tokens}
    additional_model_fields = {"top_p": top_p}

    # Send the message to the model
    response = bedrock_client.converse(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields
    )

    # Log token usage
    token_usage = response['usage']
    logger.info(f"Input tokens: {token_usage['inputTokens']}")
    logger.info(f"Output tokens: {token_usage['outputTokens']}")  # Fix: Corrected the case of the key
    logger.info(f"Total tokens: {token_usage['totalTokens']}")
    logger.info(f"Stop reason: {response['stopReason']}")

    return response

def get_feedback(bedrock_client, model_id, response, system_prompts):
    """
    Ask the model to provide feedback for the generated response.
    """
    feedback_prompt = {
        "role": "user",
        "content": [{"text": f"Provide critical feedback for the following answer:\n\n{response}"}]
    }
    feedback_response = generate_conversation(bedrock_client, model_id, system_prompts, [feedback_prompt], max_gen_len=512)
    return feedback_response['output']['message']['content'][0]['text']

def grade_response(bedrock_client, model_id, response, feedback, system_prompts):
    """
    Ask the model to grade the response on a scale from -100 to 100.
    """
    grading_prompt = {
        "role": "user",
        "content": [{"text": f"Grade the following response on a scale from -100 to 100 based on the feedback:\n\nResponse: {response}\nFeedback: {feedback}"}]
    }
    grading_response = generate_conversation(bedrock_client, model_id, system_prompts, [grading_prompt], max_gen_len=100)
    
    # Extract the number from the response text
    grading_text = grading_response['output']['message']['content'][0]['text'].strip()
    logger.info(f"Grading response: {grading_text}")

    # Use regex to extract the correct grade (ignoring "100")
    match = re.search(r'(\b-?\d{1,3}\b)(?=\s*out\s*of\s*100)', grading_text)
    if match:
        return int(match.group(0))  # Return the first matched number, which is the grade
    else:
        raise ValueError(f"Could not extract a valid grade from the response: {grading_text}")

def main(num_iterations):
    """
    Entry point for the Llama 3.1 70B model example.
    """
    model_id = "meta.llama3-70b-instruct-v1:0"

    # System prompts to guide the model's behavior
    system_prompts = [{"text": "You are a highly technical assistant providing concise and accurate reports on complex deep learning topics."}]

    # Initial message to start the conversation
    message_1 = {
        "role": "user",
        "content": [{"text": "Provide a concise and technical explanation of transformers in deep learning."}]
    }

    try:
        # Initialize the Bedrock runtime client
        bedrock_client = boto3.client(service_name='bedrock-runtime')

        # Timing start for the overall process
        start_time = time.time()

        # Open the file in write mode to empty it before writing
        with open('response.txt', 'w') as file:

            # Generate initial responses (3 responses)
            messages = [message_1]
            responses = []
            for i in range(3):
                response_start_time = time.time()
                response = generate_conversation(bedrock_client, model_id, system_prompts, messages, max_gen_len=1024)
                response_text = response['output']['message']['content'][0]['text']
                response_time_taken = time.time() - response_start_time
                responses.append({"response": response_text, "feedback": None, "grade": None, "time_taken": response_time_taken})

            # Perform feedback and grading in each iteration
            for iteration in range(num_iterations):
                logger.info(f"Iteration {iteration + 1}")
                for i, r in enumerate(responses):
                    # Get feedback for the response
                    feedback_start_time = time.time()
                    feedback = get_feedback(bedrock_client, model_id, r['response'], system_prompts)
                    feedback_time_taken = time.time() - feedback_start_time
                    responses[i]['feedback'] = feedback
                    responses[i]['feedback_time_taken'] = feedback_time_taken

                    # Grade the response based on feedback
                    grade_start_time = time.time()
                    grade = grade_response(bedrock_client, model_id, r['response'], feedback, system_prompts)
                    grade_time_taken = time.time() - grade_start_time
                    responses[i]['grade'] = grade
                    responses[i]['grade_time_taken'] = grade_time_taken

                # Sort responses by grade and refine the best response for the next iteration
                responses = sorted(responses, key=lambda x: x['grade'], reverse=True)

                logger.info(f"Best response at iteration {iteration + 1}: {responses[0]['response']} (Grade: {responses[0]['grade']})")

                # Optionally, refine the top response for the next iteration
                best_response = responses[0]['response']
                refinement_prompt = {
                    "role": "user",
                    "content": [{"text": f"Refine the following response to make it more concise and technical but retain information:\n\n{best_response}"}]
                }
                refined_response = generate_conversation(bedrock_client, model_id, system_prompts, [refinement_prompt], max_gen_len=1024)
                refined_text = refined_response['output']['message']['content'][0]['text']
                responses[0]['response'] = refined_text

            # Timing end for the overall process
            total_time_taken = time.time() - start_time

            # Write the summary to the file
            file.write("\nSUMMARY OF PROCESS\n")
            file.write("=" * 40 + "\n")
            file.write(f"Total time taken for the process: {total_time_taken:.2f} seconds\n")
            for i, r in enumerate(responses):
                file.write(f"\nResponse {i + 1}:\n")
                file.write(f"Response: {r['response']}\n")
                file.write(f"Feedback: {r['feedback']}\n")
                file.write(f"Grade: {r['grade']}\n")
                file.write(f"Response generation time: {r['time_taken']:.2f} seconds\n")
                file.write(f"Feedback generation time: {r['feedback_time_taken']:.2f} seconds\n")
                file.write(f"Grading time: {r['grade_time_taken']:.2f} seconds\n")
            file.write("=" * 40 + "\n")
            file.write(f"Best response: {responses[0]['response']} (Grade: {responses[0]['grade']})\n")

    except ClientError as err:
        logger.error(f"A client error occurred: {err.response['Error']['Message']}")
        print(f"A client error occurred: {err.response['Error']['Message']}")

if __name__ == "__main__":
    num_iterations = 3  # Set the number of iterations
    main(num_iterations)
