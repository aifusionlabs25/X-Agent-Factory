import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import json
import argparse
from utils import load_env, load_json

def generate_sales_email(vertical, pain_point, agent_name):
    print(f"📧 Sales Gen: Drafting outreach for '{vertical}'...")
    
    subject = f"Solution for {vertical} {pain_point.split(' ')[0:3]}..."
    
    body = f"""
    Subject: {subject}

    Hi there,

    I noticed that many {vertical} clinics struggle with "{pain_point}".
    
    We have built {agent_name}, an AI focused specifically on solving this.
    It handles triage and scheduling 24/7, so your staff can focus on care.

    Would you be open to a 30-second demo?

    Best,
    Forge (X Agent Factory)
    """
    
    print(body)
    return body

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python sales_generator.py <vertical> <pain_point> <agent_name>")
        # Test mode
        generate_sales_email("Veterinary", "Long hold times", "Ava")
    else:
        generate_sales_email(sys.argv[1], sys.argv[2], sys.argv[3])
