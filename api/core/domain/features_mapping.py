from core.domain.features import BaseFeature, FeatureSection, FeatureTag, FeatureWithImage

GENERATE_PRODUCT_DESCRIPTIONS_BASED_ON_IMAGE_FEATURE = BaseFeature(
    name="Generate Product Descriptions Based on Image",
    description="Create detailed product descriptions automatically from uploaded images. This agent analyzes the visual content and generates appropriate text describing the product shown, saving time on content creation while maintaining consistency across your product catalog.",
    specifications="Input: an image. Output: a description of the product shown in the image.",
)

SUMMARIZE_PDF_CONTENT_FEATURE = BaseFeature(
    name="Summarize PDF Content",
    description="Extract the key information from PDF documents with our summarization tool. This agent analyzes the full content of your PDF and generates a concise text summary highlighting the main points.",
    specifications="Input: a PDF document. Output: a summary of the content (string).",
)

GENERATE_VERSIONS_OF_SOCIAL_MEDIA_POSTS_FEATURE = BaseFeature(
    name="Generate Versions of Social Media Posts Optimized for Different Platforms",
    description="Create platform-specific variations of your social media content. Provide a topic or existing post along with your target platforms, and receive tailored versions optimized for the appropriate tone, format, and length requirements of each selected social media site.",
    specifications="Input: a topic or existing post and a list of social media sites. Output: versions of a social media post that contain the same content as the input topic and are tailored to the appropriate tone and length for each of the requested social media sites.",
)

SUMMARIZE_INSURANCE_COVERAGE_DETAILS_FROM_POLICY_DOCUMENTS_FEATURE = BaseFeature(
    name="Summarize Insurance Coverage Details From Policy Documents",
    description="Extract and organize key coverage details from insurance policy documents. This feature analyzes insurance plan information and produces a structured summary of coverage terms, limits, deductibles, and other essential policy details.",
    specifications="Input: insurance plan information in a document. Output: summary of insurance coverage details.",
)

EXTRACT_CALENDAR_EVENT_FROM_EMAIL_FEATURE = BaseFeature(
    name="Extract Calendar Event From Email",
    description="Automatically identifies and extracts calendar event details from email content. This agent analyzes the email text and organizes relevant information into structured event fields, allowing for quick transfer of meeting details to your calendar.",
    specifications="Input: a text email. Output: a calendar event (field1, field2, field3). The goal is to extract a calendar event from the email.",
)


EXTRACT_TASKS_FROM_MEETING_TRANSCRIPT_FEATURE = FeatureWithImage(
    name="Extract Tasks From a Meeting Transcript - by M1",
    description="Automatically identify and extract tasks from meeting transcripts. This agent analyzes the conversation text and generates a structured list of tasks, each with a title, description, and the original quote from which it was derived.",
    specifications="Input: a written transcript of a meeting. Output: a list of tasks extracted from the transcript. Each task should include a title, description, and a corresponding quote in the transcript.",
    image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/m1-extract-tasks-from-trancript.png",
)

EXTRACT_MEETING_NOTES_FROM_TRANSCRIPT_FEATURE = FeatureWithImage(
    name="Extract Meeting Notes from a Transcript - by M1",
    description="Transform meeting transcripts into structured notes with this feature. It analyzes transcript content and generates organized notes with clear titles and bullet-pointed details, making it easier to review and share key information from your meetings.",
    specifications="Input: a transcript of a meeting. Output: a list of notes from the content of the meeting. Each note should have a title and a body that is written in bullet point form.",
    image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/m1-extract-meeting-notes-from-transcipt.png",
)

SUMMARIZE_MEETING_CONTENT_FROM_TRANSCRIPT_FEATURE = FeatureWithImage(
    name="Summarize Meeting Content From a Transcript - by M1",
    description="Transform meeting transcripts into concise bullet-point summaries. This feature analyzes the content of your meeting transcript and generates a structured summary highlighting key points, decisions, and action items.",
    specifications="Input: (string) a transcript of a meeting. Output: (string) a summary of the meeting in bullet points.",
    image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/m1-summarize-meeting-content-from-transcript.png",
)

GENERATE_SASSY_IMAGE_DESCRIPTION_FEATURE = FeatureWithImage(
    name="Generate Sassy Image Description - by Amo",
    description="Create short, witty image descriptions with a sassy twist. This feature analyzes images and generates humorous captions (5 words maximum) that add personality while remaining appropriate.",
    specifications="Input: an image. Output: a short (5 words max) description of the image. Goal: the description should be sassy, humorous, but not offensive.",
    image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/amo-sassy-image-description.png",
)

GENERATE_SOAP_NOTES_FROM_TRANSCRIPT_FEATURE = FeatureWithImage(
    name="Generate SOAP Notes From Transcript - by Berry Street",
    description="Convert audio recordings into structured SOAP notes. This feature analyzes your audio files and automatically generates clinical documentation in the SOAP format (Subjective, Objective, Assessment, Plan), helping clinicians transform verbal sessions into organized medical records.",
    specifications="Input: an audio file. Output: SOAP notes from the audio file.",
    image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/berrystreet-generate-soap-notes-from-transcript.png",
)

GENERATE_7_DAY_MEAL_PLANNER_FEATURE = FeatureWithImage(
    name="7 Day Meal Planner - by Berry Street",
    description="Plan your entire week's meals with personalized recommendations based on your dietary needs. Specify restrictions, preferences, calorie goals, and household considerations to receive a complete 7-day plan with breakfast, lunch, dinner, and snacks. Each meal includes nutritional information with calorie count and macronutrient breakdown.",
    specifications="Goal is to create a meal plan for the week. Input: dietary restrictions and allergies (string), food preferences (string), calorie and macro requirement (string), household considerations (string). Output: breakfast, lunch, dinner, and a snack for each day of the week. Each item (breakfast, lunch, dinner, snack) should have a title (string), a description (string), the calories for the meal (number), and protein (number), fat (number), carb (number) breakdown.",
    image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/berrystreet-7-day-meal-planner.png",
)

GENERATE_SHOPPING_LIST_FROM_MEAL_PLAN_FEATURE = FeatureWithImage(
    name="Create a Shopping List From a Meal Plan - by Berry Street",
    description="Transform your meal plan into an organized shopping list. This feature takes your selected meals and recipes, then generates a complete shopping list with item names, quantities, and units for all ingredients needed.",
    specifications="Input: a list of meals (title and recipe). Output: a shopping list. Each item in the shopping list should have a name 'item', quantity, and unit.",
    image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/berrystreet-generated-shopping-list-from-meal-plan.png",
)

GENERATE_FOOD_IMAGE_JOURNALING_FEATURE = FeatureWithImage(
    name="Food Image Journaling - by Berry Street",
    description="Capture images of your meals to automatically generate detailed food descriptions and nutritional information. This tool analyzes your food photos to provide estimated calorie counts and nutrient content, helping you track your dietary intake with visual documentation.",
    specifications="Input: an image of a meal. Output: a description of the food included in the picture, along with estimated nutritional information.",
    image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/berrystreet-food-image-journaling.png",
)

SUMMARIZE_REVIEWS_FEATURE = FeatureWithImage(
    name="Summary of Reviews - by Google",
    description="Consolidates multiple Google reviews into a concise third-person summary highlighting common themes and sentiments expressed by reviewers. This provides a quick overview of collective opinions without needing to read each individual review.",
    specifications="Input: a list of reviews about a place. Output: a string that is a third-person summary of common themes expressed in the reviews.",
    image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/google-reviews-summary.png",
)

WRITTING_TOOLS_FEATURE = FeatureWithImage(
    name="Writing Tools - by Apple",
    description="Transform your writing with Apple's Writing Tools. This feature allows you to select text and apply various improvements such as summarizing into bullet points, adjusting tone (friendly or professional), making content more concise, or proofreading for errors. Simply select your text and choose the desired writing enhancement.",
    specifications="Input: a piece of writing (text, email, note, etc.), and one request for writing help (summarize into bullet points, rephrase to be more friendly, rephrase to be more professional, rephrase to be more concise, proofread). Output: updated text that is edited per the input request.",
    image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/apple-system-wide-writting-tools.png",
)

ANSWER_QUESTION_ABOUT_PRODUCT_FEATURE = FeatureWithImage(
    name="Answer Question About a Product - by Amazon",
    description="Provides answers to specific questions about Amazon products. Simply provide a product URL and your question to receive detailed information based on the product listing.",
    specifications="Input: a URL of a product, and a question about the product. Output: an answer to the question about the product.",
    image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/amazon-answer-questions-about-products.png",
)

SMART_EMAIL_RESPONSE_FEATURE = FeatureWithImage(
    name="Smart Email Response - by Google",
    description="Generate complete email responses based on short prompts. This feature analyzes your input and creates appropriate email content that matches your intended message. Simply provide a brief description of what you want to communicate, and receive a fully composed email ready to send.",
    specifications="Input: (string) a short email prompt. Output: (string) an email composed based on the content of the prompt.",
    image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/google-smart-email-response.png",
)

NOTIFICATION_SUMMARIES_FEATURE = FeatureWithImage(
    name="Notification Summaries - by Apple",
    description="Consolidates multiple notifications from the same app into a single, concise summary. The summary displays the app name as the title and presents a brief overview of all notifications in the body, making it easier to process information at a glance.",
    specifications="Input: a list of notifications texts (title, possible subtitle, body) (all from the same app). Output: a summary of all notifications, formatted like a notification. Title is the name of the app. Body is the summary (so the summary needs to be short enough to fit the notification body).",
    image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/apple-notification-summary.png",
)


GENERATE_IMAGE_FEATURE = FeatureWithImage(
    name="Generate an Image - powered by GPT-Image from OpenAI",
    description="Generate an image based on a text prompt using GPT-Image from OpenAI.",
    specifications="Input: a prompt string - field name “prompt”. Output: a generated image - field name “image”.",
    image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/image-generation.png",
)


FEATURES_MAPPING: list[FeatureSection] = [
    FeatureSection(
        name="Categories",
        tags=[
            FeatureTag(
                name="",  # Placeholder for where the company-specific features will go.
                features=[],
                kind="company_specific",
            ),
            FeatureTag(
                name="Featured",
                features=[
                    GENERATE_IMAGE_FEATURE,
                    GENERATE_PRODUCT_DESCRIPTIONS_BASED_ON_IMAGE_FEATURE,
                    SUMMARIZE_PDF_CONTENT_FEATURE,
                    GENERATE_VERSIONS_OF_SOCIAL_MEDIA_POSTS_FEATURE,
                    SUMMARIZE_INSURANCE_COVERAGE_DETAILS_FROM_POLICY_DOCUMENTS_FEATURE,
                    EXTRACT_CALENDAR_EVENT_FROM_EMAIL_FEATURE,
                    EXTRACT_TASKS_FROM_MEETING_TRANSCRIPT_FEATURE,
                    EXTRACT_MEETING_NOTES_FROM_TRANSCRIPT_FEATURE,
                    SUMMARIZE_MEETING_CONTENT_FROM_TRANSCRIPT_FEATURE,
                    GENERATE_SASSY_IMAGE_DESCRIPTION_FEATURE,
                    GENERATE_SOAP_NOTES_FROM_TRANSCRIPT_FEATURE,
                    GENERATE_7_DAY_MEAL_PLANNER_FEATURE,
                    GENERATE_SHOPPING_LIST_FROM_MEAL_PLAN_FEATURE,
                    GENERATE_FOOD_IMAGE_JOURNALING_FEATURE,
                    SUMMARIZE_REVIEWS_FEATURE,
                    WRITTING_TOOLS_FEATURE,
                    ANSWER_QUESTION_ABOUT_PRODUCT_FEATURE,
                    SMART_EMAIL_RESPONSE_FEATURE,
                    NOTIFICATION_SUMMARIES_FEATURE,
                ],
                kind="static",
            ),
            FeatureTag(
                name="E-Commerce",
                features=[
                    GENERATE_PRODUCT_DESCRIPTIONS_BASED_ON_IMAGE_FEATURE,
                    BaseFeature(
                        name="Generate Shopping List Based on a Picture of Food",
                        description="Create a shopping list by uploading a photo of a meal. This agent identifies ingredients in the image and compiles them into a ready-to-use shopping list.",
                        specifications="Input: an image containing a meal. Output: a shopping list of each item in the picture.",
                    ),
                    BaseFeature(
                        name="Generate Ad Copy Based on a Product Description",
                        description="Transform product descriptions into compelling ad copy. This feature analyzes your product information and generates targeted advertising text that highlights key selling points and benefits, helping you create effective marketing materials quickly.",
                        specifications="Input: a product description. Output: ad copy for the product described.",
                    ),
                    BaseFeature(
                        name="Extract Sentiment From Product Review",
                        description="Analyze product reviews to determine the overall sentiment expressed by customers. This feature processes review text and identifies whether the sentiment is positive, negative, or neutral, helping you understand customer satisfaction at a glance.",
                        specifications="Input: a product review. Output: the main sentiment of the review.",
                    ),
                    BaseFeature(
                        name="Summarize Common Review Sentiments",
                        description="Identify common themes and topics across multiple product reviews. This feature analyzes review content to extract recurring sentiments, helping you understand the collective customer experience without reading each review individually.",
                        specifications="Input: a list of different reviews for a product. Output: common themes and/or topics identified in the reviews.",
                    ),
                    BaseFeature(
                        name="Generate Product Recommendations Based on Purchase History",
                        description="Analyze customer purchase history to generate targeted product recommendations. This feature identifies patterns in buying behavior and suggests relevant items that align with customer preferences, increasing the likelihood of additional purchases and enhancing the shopping experience.",
                        specifications="Input: a purchase history. Output: product recommendations. Your goal is to provide the most applicable product recommendations based on an analysis of the user's purchase history.",
                    ),
                    BaseFeature(
                        name="Rewrite Product Descriptions for SEO Optimization",
                        description="Transform your product descriptions to improve search engine visibility. This feature analyzes your existing content and generates SEO-optimized versions that maintain your brand voice while incorporating relevant keywords and search-friendly structure.",
                        specifications="Input: a product description. Output: rewritten product description for SEO.",
                    ),
                    BaseFeature(
                        name="Detect Fake or Spam Reviews",
                        description="Analyze product reviews to identify potential spam or bot-generated content. This tool examines review text patterns and characteristics to flag suspicious submissions, helping maintain review quality and authenticity.",
                        specifications="Input: a product review. Output: if the review is detected as likely being spam or from a bot.",
                    ),
                    BaseFeature(
                        name="Generate Pros & Cons Lists From Customer Reviews",
                        description="Transform customer reviews into organized pros and cons lists. This feature analyzes review content to identify positive and negative product aspects, presenting them in a structured format that highlights key customer sentiments and product attributes.",
                        specifications="Input: a collection of customer reviews. Output: a list of pros and cons about the product as identified in the reviews.",
                    ),
                    BaseFeature(
                        name="Product Review Classification",
                        description="Analyze product reviews to determine their sentiment. This feature processes review text and classifies it as positive, negative, or neutral, helping businesses understand customer feedback at scale.",
                        specifications="Input: a product review. Output: the sentiment of the product review.",
                    ),
                ],
                kind="static",
            ),
            FeatureTag(
                name="Healthcare",
                features=[
                    BaseFeature(
                        name="Generate SOAP Notes From Audio",
                        description="Convert audio recordings into structured SOAP notes. This feature transcribes audio content and organizes it into the standard Subjective, Objective, Assessment, and Plan format used in clinical documentation.",
                        specifications="Input: an audio file. Output: SOAP notes from the audio file.",
                    ),
                    BaseFeature(
                        name="Generate SOAP Notes From Text Transcript",
                        description="Transform conversation transcripts into structured SOAP notes. This feature analyzes text transcripts of patient encounters and automatically organizes the information into Subjective, Objective, Assessment, and Plan sections, creating standardized clinical documentation.",
                        specifications="Input: a text transcript of a conversation. Output: SOAP notes from the text transcript.",
                    ),
                    BaseFeature(
                        name="Extract ICD-10 Codes From Transcription",
                        description="Automatically identifies and extracts ICD-10 diagnostic codes from conversation transcripts. This feature analyzes the text content to locate and compile all relevant medical coding information present in the transcript.",
                        specifications="Input: a text transcript of a conversation. Output: ICD-10 codes from content in the transcript.",
                    ),
                    BaseFeature(
                        name="Anonymize PII",
                        description="Automatically detects and anonymizes personally identifiable information (PII) within document content. This feature scans text for sensitive data such as names, addresses, phone numbers, and other personal identifiers, replacing them with generic placeholders to protect privacy while preserving document context.",
                        specifications="Input: a string (content of a document). Output: a string (updated content of the document). Goal: anonymize all PII detected in the input.",
                    ),
                    BaseFeature(
                        name="Identify Potential Allergens From Photo of Menu",
                        description="Analyze photos of restaurant menus to identify potential allergens in each dish. This feature helps users with food allergies or dietary restrictions make informed choices when dining out by highlighting ingredients that may cause allergic reactions.",
                        specifications="Input: a photo of a menu. Output: potential allergens of each item pictured in the menu photo.",
                    ),
                    BaseFeature(
                        name="Extract Data From Insurance Invoices",
                        description="Automatically extract structured data from insurance invoice documents. This agent identifies and captures policy information, charges, and invoice details, converting unstructured document content into organized, usable data.",
                        specifications="Input: insurance invoice document. Output: data from document including policy information and charges, and invoice details.",
                    ),
                    BaseFeature(
                        name="Summarize Patient Medical History From PDF Records",
                        description="Convert PDF medical records into concise patient history summaries. This feature extracts key medical information from uploaded PDF documents and generates a structured overview of the patient's health history, conditions, and treatments.",
                        specifications="Input: medical records in a PDF. Output: summary of medical history from provided records.",
                    ),
                    SUMMARIZE_INSURANCE_COVERAGE_DETAILS_FROM_POLICY_DOCUMENTS_FEATURE,
                    BaseFeature(
                        name="Classify Medical Claims by Approval Likelihood",
                        description="Analyze medical claims to determine their likelihood of approval. This feature evaluates claim details and provides an assessment of approval probability, helping to prioritize claims processing and identify potential issues before submission.",
                        specifications="Input: a medical claim. Output: how likely it is to be approved.",
                    ),
                    BaseFeature(
                        name="Generate a Meal Plan for the Week",
                        description="Create a personalized 7-day meal plan tailored to your specific needs. Specify your dietary goals, calorie requirements, food preferences, and allergies to receive a complete plan with breakfast, lunch, dinner, and snack options for each day of the week.",
                        specifications="Input: dietary/health goals, calorie count, dietary preferences, allergies. Output: a meal plan for 7 days that includes breakfast, lunch, dinner, and a snack.",
                    ),
                ],
                kind="static",
            ),
            FeatureTag(
                name="Marketing",
                features=[
                    GENERATE_PRODUCT_DESCRIPTIONS_BASED_ON_IMAGE_FEATURE,
                    BaseFeature(
                        name="Generate Ad Copy Based on a Product Description",
                        description="Transform product descriptions into compelling ad copy. This feature analyzes your product information and generates targeted advertising text that highlights key selling points and benefits, helping you create effective marketing materials quickly.",
                        specifications="Input: a product description. Output: ad copy for the product described.",
                    ),
                    BaseFeature(
                        name="Generate Blog Post",
                        description="Create complete blog posts by specifying a topic and desired tone. This agent will generate relevant content that matches your requested style, saving time while maintaining your unique voice.",
                        specifications="Input: a topic and a tone. Output: a blog post about the topic in the requested tone.",
                    ),
                    GENERATE_VERSIONS_OF_SOCIAL_MEDIA_POSTS_FEATURE,
                    BaseFeature(
                        name="Generate Engagement-Driven Email Subject Lines",
                        description="Create compelling email subject lines based on your email content. This tool analyzes your message body and generates subject lines designed to increase open rates and reader engagement while maintaining authenticity.",
                        specifications="Input: the body of an email. Output: a subject line for the email that is focused on driving authentic engagement with the email.",
                    ),
                    BaseFeature(
                        name="Summarize Common Review Sentiments",
                        description="Identify common themes and topics across multiple product reviews. This feature analyzes review content to extract recurring sentiments, helping you understand the collective customer experience without reading each review individually.",
                        specifications="Input: a list of different reviews for a product. Output: common themes and/or topics identified in the reviews.",
                    ),
                    BaseFeature(
                        name="Summarize Industry Trends From News and Reports",
                        description="Analyze news articles and industry reports to identify emerging patterns and developments. This feature extracts key trends from multiple sources, providing a consolidated view of market movements and sector-specific insights.",
                        specifications="Input: news and reports from various sources. Output: industry trends detected in the input content.",
                    ),
                    BaseFeature(
                        name="Extract Key Selling Points From Product Descriptions",
                        description="Analyze product descriptions to identify and extract the most compelling selling points. This tool transforms lengthy product text into concise, marketable highlights that can be used in promotional materials, product pages, or sales pitches.",
                        specifications="Input: a product description. Output: key selling points to highlight about the product.",
                    ),
                ],
                kind="static",
            ),
            FeatureTag(
                name="Productivity",
                features=[
                    BaseFeature(
                        name="Summarize Emails",
                        description="Condense the content of one or more emails into a concise summary. This feature extracts key information from email text and presents the main points in a clear, abbreviated format.",
                        specifications="Input: at least one email (emails are formatted as strings). Output: a summary. The goal is to provide a summary for the input email(s).",
                    ),
                    BaseFeature(
                        name="Proofread Text for Grammar/Spelling",
                        description="Automatically checks and corrects grammar and spelling errors in your text. This agent analyzes the provided content and returns a polished version with proper spelling and grammatical structure, helping you deliver error-free writing.",
                        specifications="Input: a piece of text. Output: the text with corrected grammar and spelling.",
                    ),
                    BaseFeature(
                        name="Given a Document, Generate an FAQ",
                        description="Transform your document into a comprehensive FAQ. This feature analyzes your document content and automatically generates relevant questions and answers, helping to highlight key information and create a structured reference for readers.",
                        specifications="Input: a document. Output: an FAQ based on the content of the document.",
                    ),
                    BaseFeature(
                        name="Translate PDF Content",
                        description="Convert PDF documents from one language to another. Upload your PDF file, select the target language, and receive a translated version of the content.",
                        specifications="Input: a PDF and a language. Output: the content of the PDF translated into the provided language.",
                    ),
                    BaseFeature(
                        name="Translate Text Into Another Language",
                        description="Convert your text from one language to another. Simply provide the text you want to translate and select your target language to receive the translated version.",
                        specifications="Input: some text and a language. Output: the text translated into the provided language.",
                    ),
                    BaseFeature(
                        name="Summarize Daily News Reports",
                        description="Consolidate multiple daily news reports into a concise summary. This feature processes various news inputs and generates a comprehensive overview, capturing key information from all sources in a single, readable format.",
                        specifications="Input: various news reports for a day. Output: a string. The string should be a summary of the news reports. The goal is to summarize a list of reports into a single string.",
                    ),
                    BaseFeature(
                        name="Extract Todos From Meeting Notes",
                        description="Automatically identifies and extracts action items from your meeting notes. This feature analyzes the content of your notes and compiles a structured list of todos, helping you track commitments and follow-up tasks discussed during meetings.",
                        specifications="Input: notes from a meeting. Output: todos that were included in the meeting notes.",
                    ),
                    BaseFeature(
                        name="Generate Follow-Up Email Suggestions From Meeting Notes",
                        description="Create targeted follow-up email suggestions based on your meeting notes. This feature analyzes the content of your notes to identify action items, commitments, and key discussion points that require email follow-up, helping you maintain clear communication and accountability after meetings.",
                        specifications="Input: notes from a meeting. Output: suggestions for follow-up emails that need to be sent.",
                    ),
                    EXTRACT_CALENDAR_EVENT_FROM_EMAIL_FEATURE,
                    BaseFeature(
                        name="Draft Message Response Based on Previous Messages (Email, Text)",
                        description="Generate a contextually appropriate response to the most recent message in a conversation thread. This feature analyzes the history of messages between two people (via email or text) and creates a relevant reply that continues the conversation naturally based on the previous exchanges.",
                        specifications="Input: thread of messages between two people (email or text, for example). Output: a message response to the most recent message. Message authors should NOT be a user/assistant thread.",
                    ),
                    BaseFeature(
                        name="Generate a SWOT Analysis",
                        description="Create a comprehensive SWOT Analysis that identifies Strengths, Weaknesses, Opportunities, and Threats for any company. Simply provide a company name to receive a structured analysis that helps with strategic planning and decision-making.",
                        specifications="Input: a company name. Output: a SWOT analysis.",
                    ),
                    BaseFeature(
                        name="Extract Meeting Link From Email",
                        description="Automatically identifies and extracts virtual meeting link URLs from emails, including calendar invitations. This feature scans the email content to locate and present any meeting links, saving you the time of manually searching through the message.",
                        specifications="Input: an email (could be an email of a calendar invite). Output: any virtual meeting link URLs detected in the message.",
                    ),
                    BaseFeature(
                        name="Language Style Detection",
                        description="Analyzes text passages to identify the writing style. Categorizes content as casual, formal, neutral, or academic based on linguistic patterns and vocabulary usage.",
                        specifications="Input: a passage of writing. Output: the style of text (casual, formal, neutral, academic).",
                    ),
                    BaseFeature(
                        name="Extract Verification Code From a Text Message",
                        description="Automatically identifies and extracts verification codes from text messages. This feature analyzes message content to locate numeric or alphanumeric verification codes, saving you the step of manually finding and copying codes when authenticating accounts or verifying transactions.",
                        specifications="Input: a text message. Output: any verification code detected.",
                    ),
                ],
                kind="static",
            ),
            FeatureTag(
                name="Social",
                features=[
                    BaseFeature(
                        name="Classify Messages as Appropriate or Not",
                        description="Analyze messages to determine appropriateness based on content evaluation. This agent identifies potentially problematic elements such as hateful language, discriminatory sentiment, or inappropriate terminology, and provides reasoning for the classification result.",
                        specifications="Input: a message. Output: whether it is appropriate or not and why. Should be based on whether there is hateful or discriminatory language or sentiment, inappropriate words, etc.",
                    ),
                    BaseFeature(
                        name="Evaluate Quality of Chatbot Response",
                        description="Analyze the quality of chatbot responses based on the conversation context. This feature evaluates how well a chatbot's reply addresses the user's needs, providing objective assessment of response relevance, accuracy, and appropriateness.",
                        specifications="Input: a chatbot response and previous context on what the response is in regard to. Output: the quality of the response.",
                    ),
                    BaseFeature(
                        name="Classify Images as Appropriate or Not",
                        description="Analyze images to determine their appropriateness. This feature evaluates visual content and provides a classification result along with reasoning for the determination, helping users identify suitable imagery for their intended use.",
                        specifications="Input: an image. Output: whether the image is appropriate or not and the reason why.",
                    ),
                    BaseFeature(
                        name="Create Quizzes From Content",
                        description="Generate multiple-choice quizzes on any topic or person. Simply provide a subject, and receive a ready-to-use quiz with questions and answer options to test knowledge or facilitate learning.",
                        specifications="Input: a topic or person. Output: a quiz with multiple-choice answers about the input topic.",
                    ),
                    GENERATE_VERSIONS_OF_SOCIAL_MEDIA_POSTS_FEATURE,
                    BaseFeature(
                        name="Detect Bot/Spam Posts",
                        description="Analyzes social media posts to identify content generated by automated bots or spam sources. This tool examines message patterns and characteristics to determine if a post is likely automated or unwanted promotional content rather than genuine user communication.",
                        specifications="Input: a social media post. Output: if the message is detected to be from a bot or is spam.",
                    ),
                    BaseFeature(
                        name="Detect Misinformation",
                        description="Analyze social media posts to identify potential misinformation. When detected, this feature highlights inaccurate content and provides factual corrections with references to reliable sources, helping users distinguish between accurate and misleading information.",
                        specifications="Input: a social media post. Output: if misinformation is detected, what is incorrect, and a reliable source referencing the truth.",
                    ),
                    BaseFeature(
                        name="Summarize Long Social Media Posts",
                        description="Condenses lengthy social media posts into concise summaries, capturing key points and main ideas. This helps users quickly understand the content without reading the entire post.",
                        specifications="Input: a post from social media. Output: a summary of the input post.",
                    ),
                    BaseFeature(
                        name="Create a Chatbot",
                        description="Create an AI chatbot that responds to user messages. This feature processes a conversation history between a user and an AI assistant, then generates the next appropriate AI response based on the context of the conversation.",
                        specifications="Input: a list of messages between a user and an AI assistant, with the last message being from the user. Output: the next response from the agent.",
                    ),
                    BaseFeature(
                        name="Create a Horoscope",
                        description="Generate a personalized daily horoscope based on your birth date and location. This feature analyzes your astrological chart to provide specific insights and predictions for today, tailored to your unique celestial positioning at birth.",
                        specifications="Input: a birthday and a location (string). Output: a horoscope for today for the astrological chart that matches the birthday/location from the input.",
                    ),
                    BaseFeature(
                        name="Generate the Next Move on a Chess Board",
                        description="Analyze the current chess board state and receive a recommended next move. This feature evaluates the position and suggests a strategic move based on the current game state.",
                        specifications="Input: a chess board state. Output: the next move.",
                    ),
                ],
                kind="static",
            ),
            FeatureTag(
                name="Developer Tools",
                features=[
                    BaseFeature(
                        name="Natural Language SQL Query",
                        description="Convert natural language questions into SQL queries. This feature transforms your text-based questions into structured database queries, allowing you to extract information from your database using everyday language rather than SQL syntax.",
                        specifications="Input: a string in natural language. Output: a SQL query. Goal: convert the natural language query into a valid SQL query.",
                    ),
                    BaseFeature(
                        name="Create Bug Ticket Titles From Slack Messages",
                        description="Generate concise and relevant bug ticket titles for project management systems like Linear or Jira directly from Slack messages. This feature analyzes the content of a Slack message and creates an appropriate title that accurately represents the issue being reported.",
                        specifications="Input: a single Slack message. Output: a project management (Linear, Jira) ticket title. Goal: compose an appropriate title for an issue that is opened based on the content of the Slack message.",
                    ),
                    BaseFeature(
                        name="Identify Prompt Injection",
                        description="Analyzes text to detect potential prompt injection attempts. This security feature examines input for manipulative instructions that might override system prompts or extract unauthorized information, providing clear reasoning for its determination.",
                        specifications="Input: a prompt. Output: whether it is a case of prompt injection or not and why.",
                    ),
                    BaseFeature(
                        name="Summarize Code Changes From a Git Diff",
                        description="Analyze code changes between two versions and generate a concise summary suitable for commit messages. This tool helps developers document their changes by identifying key modifications and presenting them in a clear, structured format.",
                        specifications="Input: two blocks of code (before change and after change). Output: a summary of the changes for a commit message.",
                    ),
                    BaseFeature(
                        name="Convert Regular Expressions Into Human-Readable Explanations",
                        description="Transform complex regular expressions into clear, human-readable explanations. This feature analyzes regex patterns and provides a plain English interpretation of what the expression is designed to match.",
                        specifications="Input: a regular expression. Output: an explanation of the regular expression in plain English.",
                    ),
                    BaseFeature(
                        name="Explain a Code Snippet in Plain Language",
                        description="Converts complex code snippets into clear, plain language explanations. This feature analyzes the provided code and generates a human-readable description of what the code does, making it easier to understand programming logic without technical expertise.",
                        specifications="Input: a code snippet. Output: an explanation of the code snippet's functionality in plain English.",
                    ),
                    BaseFeature(
                        name="Generate Unit Test Cases From Function Definitions",
                        description="Create comprehensive unit test cases directly from your function definitions. This feature analyzes the function signature and purpose to generate appropriate test cases that verify the function's behavior across various inputs and edge cases.",
                        specifications="Input: a function definition. Output: unit tests for the given function.",
                    ),
                    BaseFeature(
                        name="Generate Code Documentation From Inline Code Comments",
                        description="Transform your inline code comments into comprehensive documentation. This feature analyzes your code and extracts meaningful information from comments to create structured documentation that helps maintain code clarity and improves collaboration among developers.",
                        specifications="Input: some code. Output: documentation for the code, based on the inline comments.",
                    ),
                    BaseFeature(
                        name="Generate Code",
                        description="Create functional code snippets by providing a description of what you need and your preferred programming language. This agent will generate code that implements your requirements in the specified language.",
                        specifications="Input: explanation of what you want a code function to accomplish and a coding language. Output: code accomplishing the request in the requested language.",
                    ),
                ],
                kind="static",
            ),
        ],
    ),
    FeatureSection(
        name="Inspired by",
        tags=[
            FeatureTag(
                name="Apple, Google, Amazon",
                features=[
                    ANSWER_QUESTION_ABOUT_PRODUCT_FEATURE,
                    FeatureWithImage(
                        name="Review Highlights - by Amazon",
                        description="Summarizes common themes from multiple Amazon product reviews into a concise third-person overview. This feature identifies recurring points mentioned across reviews and presents them as a structured summary, helping users quickly understand collective customer experiences.",
                        specifications="Input: a list of reviews about a product. Output: a string that is a third-person summary of common themes expressed in the reviews.",
                        image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/amazon-create-with-alexa.png",
                    ),
                    FeatureWithImage(
                        name="Story Creation - by Amazon",
                        description="Create personalized stories based on your prompts, tailored to your child's age group. Simply provide a story idea and your child's age, and receive a custom narrative designed specifically for their developmental stage and interests.",
                        specifications="Input: a story prompt, and the age of the target child. Output: a story based on the prompt and written for the appropriate age group.",
                        image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/amazon-review-highlights.png",
                    ),
                    WRITTING_TOOLS_FEATURE,
                    NOTIFICATION_SUMMARIES_FEATURE,
                    FeatureWithImage(
                        name="Priority Messages and Intelligent Email Summaries - by Apple",
                        description="Automatically identifies high-priority emails in your inbox and generates concise summaries of each message. This feature analyzes your incoming mail to help you quickly identify important communications and understand message content without opening each email.",
                        specifications="Input: a list of emails. Output: the priority of each email and a summary of each email.",
                        image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/apple-priority-message-and-intelligent-email-summaries.png",
                    ),
                    SUMMARIZE_REVIEWS_FEATURE,
                    SMART_EMAIL_RESPONSE_FEATURE,
                    FeatureWithImage(
                        name="Summarize in Recorder - by Google",
                        description="Convert audio files into text with Google's Recorder app. This feature automatically generates both a concise summary and a complete transcription of your audio content, making it easier to review and reference recorded information.",
                        specifications="Input: an audio file. Output: a summary of the audio file and a full transcription of the audio file.",
                        image_url="https://workflowai.blob.core.windows.net/workflowai-public/landing-page-features/google-summarize-in-recorder.png",
                    ),
                ],
                kind="static",
            ),
            FeatureTag(
                name="Our Customers",
                features=[
                    EXTRACT_MEETING_NOTES_FROM_TRANSCRIPT_FEATURE,
                    EXTRACT_TASKS_FROM_MEETING_TRANSCRIPT_FEATURE,
                    SUMMARIZE_MEETING_CONTENT_FROM_TRANSCRIPT_FEATURE,
                    GENERATE_SASSY_IMAGE_DESCRIPTION_FEATURE,
                    GENERATE_SOAP_NOTES_FROM_TRANSCRIPT_FEATURE,
                    GENERATE_7_DAY_MEAL_PLANNER_FEATURE,
                    GENERATE_SHOPPING_LIST_FROM_MEAL_PLAN_FEATURE,
                    GENERATE_FOOD_IMAGE_JOURNALING_FEATURE,
                ],
                kind="static",
            ),
        ],
    ),
    FeatureSection(
        name="Use Cases",
        tags=[
            FeatureTag(
                name="PDFs and Documents",
                features=[
                    BaseFeature(
                        name="Translate PDF Content",
                        description="Convert PDF documents from one language to another. Upload your PDF file, select the target language, and receive a translated version of the content.",
                        specifications="Input: a PDF and a language. Output: the content of the PDF translated into the provided language.",
                    ),
                    BaseFeature(
                        name="Summarize Patient Medical History From PDF Records",
                        description="Convert PDF medical records into concise patient history summaries. This feature extracts key medical information from uploaded PDF documents and generates a structured overview of the patient's health history, conditions, and treatments.",
                        specifications="Input: medical records in a PDF. Output: summary of medical history from provided records.",
                    ),
                    BaseFeature(
                        name="Extract Data From Insurance Invoices",
                        description="Automatically extract structured data from insurance invoice documents. This agent identifies and captures policy information, charges, and invoice details, converting unstructured document content into organized, usable data.",
                        specifications="Input: insurance invoice document. Output: data from document including policy information and charges, and invoice details.",
                    ),
                    SUMMARIZE_INSURANCE_COVERAGE_DETAILS_FROM_POLICY_DOCUMENTS_FEATURE,
                    SUMMARIZE_PDF_CONTENT_FEATURE,
                    BaseFeature(
                        name="Generate an FAQ From a Document",
                        description="Transform your document into a comprehensive FAQ. This feature analyzes your document content and automatically creates relevant question-answer pairs that capture key information, making complex content more accessible and easier to navigate.",
                        specifications="Input: a document. Output: an FAQ based on the content of the document.",
                    ),
                    BaseFeature(
                        name="Extract Legal Document Risks",
                        description="Analyze legal documents and contracts to identify potential risks and important clauses requiring attention. This tool examines PDF documents and generates a comprehensive list of concerning elements that merit review before signing, helping to highlight critical information that might otherwise be overlooked.",
                        specifications="Input: a PDF of a legal document or contract. Output: a list of potentially concerning or important information that should be reviewed before signing the document.",
                    ),
                    BaseFeature(
                        name="Detect Plagiarism in PDF Document",
                        description="Analyze PDF documents to identify potential plagiarism. This tool examines essay content and highlights any detected instances of plagiarized material, providing specific details about the copied content.",
                        specifications="Input: a PDF document of an essay. Output: if plagiarism is detected and what is being plagiarized.",
                    ),
                    BaseFeature(
                        name="Compare Job Posting Requirements With Resume",
                        description="Analyze how well your resume matches a job posting by providing both your resume PDF and the job posting URL. This agent compares your qualifications against the job requirements, identifies matching strengths, and highlights any key qualifications missing from your resume to help you assess fit and tailor your application.",
                        specifications="Input: a resume PDF and a URL of a job description. Output: summary of if the job requirements are a good fit for the resume, highlights of where the resume/JD match, and key items missing on the resume.",
                    ),
                    BaseFeature(
                        name="Extract Answer From PDF",
                        description="Extract specific information from PDF documents by asking questions. This feature analyzes the content of your PDF and provides relevant answers based on the document's text, helping you quickly find information without reading the entire file.",
                        specifications="Input: a PDF and a question. Output: answer to the question, based on the content of the PDF.",
                    ),
                ],
                kind="static",
            ),
            FeatureTag(
                name="Scraping",
                features=[
                    BaseFeature(
                        name="Extract Listing Details From a Real Estate Website",
                        description="Automatically extract key information from real estate listing URLs. This feature parses the webpage content to identify and organize essential property details including description, address, price, square footage, and room counts into structured data.",
                        specifications="Input: the URL of a real estate listing (HTML formatting). Output: details of the real estate listing, including description (string), address (string), price, square feet, number of bedrooms and bathrooms.",
                    ),
                    BaseFeature(
                        name="Analyze a Company’s Blog for Content Trends",
                        description="Discover content patterns from any company blog with a simple URL input. This tool identifies recurring themes, highlights trending topics, and calculates the average publishing frequency. Gain valuable insights into a company's content strategy and focus areas through automated blog analysis.",
                        specifications="Input: the URL of a company's blog. Output: a list of common themes in their writing (list of strings), a list of trends they discuss (list of strings), and overall post publishing frequency (e.g., 'every 24 days').",
                    ),
                    BaseFeature(
                        name="Summarize Reviews From a Product",
                        description="Analyze product reviews from a URL and generate a concise summary of common sentiments. This tool extracts key opinions and recurring themes from customer feedback, helping you quickly understand the overall reception of a product without reading every review.",
                        specifications="Input: a URL for a product’s reviews page URL. Output: summary of the common sentiments.",
                    ),
                    BaseFeature(
                        name="Extract Fashion Trends From Retailer’s “New Arrivals” Page",
                        description="Analyze a fashion retailer's 'New Arrivals' page to identify current fashion trends. Simply provide the URL, and receive a comprehensive analysis of emerging styles, patterns, colors, and design elements represented in the latest merchandise.",
                        specifications="Input: a fashion retailer's 'new arrivals' page URL. Output: fashion trends based on the items displayed. Don't include a frequency number - it doesn't make sense",
                    ),
                    BaseFeature(
                        name="Compare Rental Listings",
                        description="Compare multiple rental listings side by side to evaluate key factors such as price, square footage, number of bedrooms and bathrooms, walkability scores, and pet policies. This tool helps you make informed decisions by highlighting the differences between properties.",
                        specifications="Input: 2 or more URLs of rental listings. Output: comparison of the listing including: price, sq ft., # of bedrooms, # bathrooms, location walkability, pet friendly etc.",
                    ),
                    BaseFeature(
                        name="Compare Job Posting Requirements with Resume",
                        description="Analyze how well your resume matches a job posting by providing both your resume PDF and the job posting URL. This agent identifies matching qualifications and highlights any key requirements missing from your resume, helping you determine if the position aligns with your experience.",
                        specifications="Input: a resume PDF and a URL of a job description. Output: summary of if the job reqs are a good fit for the resume, highlights of where the resume/JD match and key items missing on the resume.",
                    ),
                    BaseFeature(
                        name="Summarize News Website Headlines",
                        description="Analyze news website headlines by providing a URL. The feature generates a concise summary of the main headlines and identifies any potential bias in the reporting. This helps users quickly understand the key news topics and evaluate the objectivity of the content.",
                        specifications="Input: a news website URL. Output: summary of headlines and whether there is an evident bias detected in what is being reported.",
                    ),
                    BaseFeature(
                        name="Extract Popular Dishes From Restaurant Reviews Page",
                        description="Analyze restaurant review pages to identify the most frequently mentioned and positively reviewed dishes. Simply provide a URL to a restaurant's review page (such as Google Reviews or Yelp), and receive a list of the standout menu items based on customer feedback.",
                        specifications="Input: URL of a restaurant's reviews page (ex. Google reviews, yelp). Output: the most highly spoken of dishes in the reviews (no need to include a sentiment enum - it should be assumed that the output dishes are all highly spoken of)",
                    ),
                ],
                kind="static",
            ),
            FeatureTag(
                name="Image",
                features=[
                    GENERATE_IMAGE_FEATURE,
                    BaseFeature(
                        name="Generate Description Based on Image",
                        description="Create detailed product descriptions automatically from images. This feature analyzes uploaded product photos and generates accurate text descriptions, saving time on content creation while ensuring consistent product information.",
                        specifications="Input: an image. Output: a description of the product shown in the image.",
                    ),
                    BaseFeature(
                        name="Classify Images as Appropriate or Not",
                        description="Analyze images to determine their appropriateness. This feature evaluates visual content and provides a classification result along with reasoning for the determination, helping users identify suitable imagery for their intended use.",
                        specifications="Input: image. Output: whether the image is appropriate or not and the reason why.",
                    ),
                    BaseFeature(
                        name="Generate Shopping List Based on a Picture of Food",
                        description="Create a shopping list by uploading a photo of a meal. This agent identifies ingredients in the image and compiles them into a ready-to-use shopping list.",
                        specifications="Input: an image containing a meal. Output: a shopping list of each item in the picture.",
                    ),
                    BaseFeature(
                        name="Extract Receipt Details From Image",
                        description="Automatically extract key information from receipt images. This agent identifies vendor details, transaction date and time, reference numbers, and currency. It also captures itemized purchases with quantities and prices, along with total amounts. This functionality supports multiple currencies and provides structured data from your receipt images.",
                        specifications="Input: image of a receipt. Output: vendor information (name and address), date and time receipt was created at, reference number, currency (enum w USD|EUR|JPY|GBP|AUD|CAD|CHF|CNY|SEK|NZD|MXN|SGD|HKD|NOK|KRW|TRY|INR|RUB|BRL|ZAR|DKK|PLN|THB|IDR|MYR|VND), list of each item (name, quantity, gross and net price), total net and gross price.",
                    ),
                    GENERATE_PRODUCT_DESCRIPTIONS_BASED_ON_IMAGE_FEATURE,
                    BaseFeature(
                        name="Generate the Location of a Given Image",
                        description="Identify the city and country shown in an uploaded image. This feature analyzes visual elements in photographs to determine geographic locations, helping users identify where pictures were taken.",
                        specifications="Input: an image of a location. Output: the city and country shown in the image.",
                    ),
                    BaseFeature(
                        name="Generate the Author or Photographer of an Image",
                        description="Identify the creator behind visual art. This feature analyzes paintings and photographs to determine the artist or photographer responsible for the work. Simply upload an image, and receive information about who created it.",
                        specifications="Input: an image of a painting or photograph. Output: the painter or photographer who created the art.",
                    ),
                    BaseFeature(
                        name="Translate Text From Image",
                        description="Extract text from images and translate it into your chosen language. This feature processes visual content, identifies written text, and converts it to your specified language, enabling you to understand text in photos regardless of the original language.",
                        specifications="Input: an image containing writing and a language. Output: translate the writing in the image into the language input.",
                    ),
                    BaseFeature(
                        name="Identify Potential Allergens From Photo of Menu",
                        description="Analyze photos of restaurant menus to identify potential allergens in each dish. This feature helps users with food allergies or dietary restrictions make informed choices when dining out by highlighting ingredients that may cause allergic reactions.",
                        specifications="Input: a photo of a menu. Output: potential allergens of each item pictured in the menu photo.",
                    ),
                ],
                kind="static",
            ),
            FeatureTag(
                name="Audio",
                features=[
                    BaseFeature(
                        name="Analyze Calls to Extract User Feedback",
                        description="Automatically extract valuable user feedback from call recordings. This feature processes audio files of customer calls and identifies key feedback points, helping you gather insights without manual review of each conversation.",
                        specifications="Input: an audio file of a call. Output: extract user feedback from the audio file.",
                    ),
                    BaseFeature(
                        name="Generate SOAP Notes From Audio",
                        description="Convert audio recordings into structured SOAP notes. This feature transcribes audio content and organizes it into the standard Subjective, Objective, Assessment, and Plan format used in clinical documentation.",
                        specifications="Input: an audio file. Output: SOAP notes from the audio file.",
                    ),
                    BaseFeature(
                        name="Summarize Audio File Content",
                        description="Convert audio files into concise text summaries. This feature analyzes the content of your audio recordings and generates a condensed overview of the key information, making it easier to review and reference audio content without listening to the entire file.",
                        specifications="Input: an audio file. Output: a summary of the content of the audio file.",
                    ),
                    BaseFeature(
                        name="Generate Email From Spoken Notes",
                        description="Convert your spoken notes into email drafts. Record your thoughts, instructions, or messages as audio, and this agent will transform them into structured email content ready for review and sending.",
                        specifications="Input: an audio file of spoken notes. Output: an email draft based on the content of the spoken note.",
                    ),
                    BaseFeature(
                        name="Transcribe Text From Audio",
                        description="Convert spoken content from audio files into written text. This feature processes audio input and produces a text transcription of the speech contained within the file, allowing you to capture and read audio content.",
                        specifications="Input: an audio file. Output: a transcription (string) of the content of the audio file.",
                    ),
                    BaseFeature(
                        name="Generate To-Do List From Meeting Recording",
                        description="Extract action items and follow-up tasks directly from your meeting recordings. This feature analyzes the audio content of your meetings and compiles a structured to-do list based on commitments and action items discussed during the conversation.",
                        specifications="Input: an audio file recording of a meeting. Output: any to-dos/follow-ups discussed in the meeting.",
                    ),
                    BaseFeature(
                        name="Extract Quotable Statements From Interviews",
                        description="Automatically identify and extract notable quotes from interview recordings. This feature analyzes audio content to isolate significant statements made by the interviewee, providing you with ready-to-use quotes without manual transcription or review.",
                        specifications="Input: an audio recording of an interview. Output: quotable statements from the person being interviewed.",
                    ),
                    BaseFeature(
                        name="Extract Study Notes From College Lecture",
                        description="Transform your college lecture recordings into organized study notes. This feature analyzes audio recordings of lectures and generates structured notes highlighting key concepts, definitions, and important points discussed during class, providing you with ready-to-use study materials.",
                        specifications="Input: an audio recording of a college lecture. Output: notes from the lecture to study from.",
                    ),
                    BaseFeature(
                        name="Extract FAQs From Customer Call Transcripts",
                        description="Analyze customer call recordings to identify and compile frequently asked questions. This feature processes audio files of customer interactions and generates a structured list of common inquiries, helping teams understand recurring customer concerns and information needs.",
                        specifications="Input: audio files of customer calls. Output: a list of frequently asked questions detected throughout the recordings.",
                    ),
                ],
                kind="static",
            ),
        ],
    ),
]
