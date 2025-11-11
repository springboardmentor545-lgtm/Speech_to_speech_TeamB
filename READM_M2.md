# **README – Milestone 2: AI-Powered Real-Time Speech Translation for Multilingual Content**

---

## **Project Overview**

This project aims to develop an **AI-powered real-time speech-to-speech translation system** that converts live English/Hindi commentary into **12+ global languages**.  
The system leverages **Microsoft Azure Speech-to-Text**, **Azure OpenAI**, and **Translation APIs** to ensure seamless integration into OTT (Over-The-Top) media platforms, enhancing multilingual accessibility.

---

## **Milestone 2 Objective**

**Milestone 2** focuses on the **Translation Model Development and Training** phase.  
The primary goal is to build, train, and validate translation models capable of converting live-transcribed speech into multiple languages in real time.

---

## **Key Tasks Completed**

### **1. Model Selection & Setup**
- Evaluated Azure OpenAI models optimized for speed and translation accuracy.  
- Configured Azure Translation APIs and integrated them with the project pipeline.

### **2. Pipeline Integration**
- Connected Milestone 1’s speech-to-text output as input to the translation module.  
- Established API calls via Python to perform multilingual translation dynamically.

### **3. Speech Synthesis**
- Integrated Azure Speech Synthesis for text-to-speech output.  
- Enabled realistic, natural-sounding voices using neural speech models.

### **4. Evaluation & Optimization**
- Measured model performance using **BLEU Score** (for translation accuracy) and **Latency** (for response time).  
- Fine-tuned prompts and added **custom glossaries** for domain-specific terms (sports/news).

---

## **Tools & Technologies**

| **Category** | **Tools / Libraries** |
|---------------|-----------------------|
| **Cloud & AI Services** | Microsoft Azure OpenAI, Azure Speech-to-Text, Azure Translation, Azure Speech Synthesis |
| **Programming Languages** | Python, Node.js |
| **Libraries** | pydub, requests, wave, json |
| **Evaluation Metrics** | BLEU Score (accuracy), Latency (speed) |

---

## **Challenges & Solutions**

| **Challenge** | **Solution** |
|----------------|--------------|
| High translation latency | Used streaming APIs and neural voices to reduce delay to ~2.4 seconds. |
| Inaccurate translation of domain-specific terms | Created a custom glossary and fine-tuned Azure OpenAI models. |
| Robotic speech synthesis | Adjusted system prompts for a more natural and conversational tone. |

---

## **Performance Summary**

- **BLEU Score:** 93.89%  
- **Average Latency:** 2.4s  
- **Languages Supported:** 12+  
- **Status:**  Successfully completed and validated translation pipeline.

---

## **Key Learnings**

- Implementing real-time API-based translation workflows using Azure SDKs.  
- Optimizing pipelines for **low-latency**, real-time speech-to-speech translation.  
- Fine-tuning GPT-based translation models for domain accuracy.  
- Evaluating machine translation using BLEU metrics.

---

## **Next Steps (Milestone 3 Preview)**

- Integrate the translation pipeline into the OTT platform.  
- Build a user interface for **language selection and playback**.  
- Conduct load and **User Acceptance Testing (UAT)**.  
- Finalize deployment and system documentation.

---

**_End of Milestone 2 Documentation_**
