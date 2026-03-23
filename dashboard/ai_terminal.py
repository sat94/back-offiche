import json
import urllib.request
from decouple import config

DEEPINFRA_URL = 'https://api.deepinfra.com/v1/openai/chat/completions'
MODEL = 'anthropic/claude-4-sonnet'

SYSTEM_PROMPT = """Tu es un administrateur système Linux expert. Tu aides l'utilisateur à gérer ses serveurs via SSH.

RÈGLES STRICTES :
1. Quand l'utilisateur demande une action, réponds avec un JSON contenant les commandes à exécuter
2. Format de réponse OBLIGATOIRE quand des commandes sont nécessaires :
   {"commands": ["cmd1", "cmd2"], "explanation": "explication courte"}
3. Si c'est juste une question d'interprétation de résultats, réponds en texte normal (pas de JSON)
4. N'utilise JAMAIS de commandes destructives sans que l'utilisateur l'ait explicitement demandé (rm -rf, dd, mkfs, etc.)
5. Préfère les commandes non-interactives (ajoute -y pour apt, utilise sed au lieu de nano, etc.)
6. Pour les commandes longues, ajoute des timeouts ou limites
7. Sois concis dans tes explications

CONTEXTE : Les serveurs sont sous Ubuntu/Debian. L'utilisateur est root sur la plupart des serveurs."""


_conversations = {}


def chat(session_id, user_message, command_output=None):
    api_key = config('DEEPINFRA_API_KEY')

    if session_id not in _conversations:
        _conversations[session_id] = []

    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]

    if command_output is not None:
        _conversations[session_id].append({
            'role': 'user',
            'content': f"Résultat de l'exécution :\n```\n{command_output}\n```\nAnalyse ce résultat."
        })
    else:
        _conversations[session_id].append({
            'role': 'user',
            'content': user_message
        })

    messages.extend(_conversations[session_id][-20:])

    payload = json.dumps({
        'model': MODEL,
        'messages': messages,
        'max_tokens': 2048,
        'temperature': 0.3,
    }).encode()

    req = urllib.request.Request(DEEPINFRA_URL, data=payload, headers={
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    })

    resp = urllib.request.urlopen(req, timeout=60)
    body = json.loads(resp.read())

    assistant_msg = body['choices'][0]['message']['content']

    _conversations[session_id].append({
        'role': 'assistant',
        'content': assistant_msg
    })

    commands = None
    explanation = None
    try:
        start = assistant_msg.find('{')
        end = assistant_msg.rfind('}') + 1
        if start >= 0 and end > start:
            parsed = json.loads(assistant_msg[start:end])
            if 'commands' in parsed and isinstance(parsed['commands'], list):
                commands = parsed['commands']
                explanation = parsed.get('explanation', '')
    except (json.JSONDecodeError, KeyError):
        pass

    return {
        'response': assistant_msg,
        'commands': commands,
        'explanation': explanation,
    }


def clear_conversation(session_id):
    _conversations.pop(session_id, None)
