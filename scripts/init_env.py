"""Generate local secrets without printing them. Existing .env is preserved."""
import base64
import secrets
from pathlib import Path

root=Path(__file__).resolve().parents[1]
path=root/'.env'
if not path.exists():
    path.write_text('POSTGRES_USER=music_admin\nPOSTGRES_PASSWORD='+secrets.token_hex(24)+'\nAIRFLOW__API_AUTH__JWT_SECRET='+secrets.token_hex(32)+'\nAIRFLOW__CORE__FERNET_KEY='+base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()+'\n',encoding='utf-8')
for name in ['data','logs','docs/evidence','notebooks','tests']:
    (root/name).mkdir(parents=True,exist_ok=True)
print('Local configuration ready; credentials are not displayed.')
