import express from 'express';
import qrcode from 'qrcode';
import pkg from 'whatsapp-web.js';
const { Client, LocalAuth } = pkg;

const PORT = process.env.BRIDGE_PORT || 3001;
const DJANGO_WEBHOOK = process.env.DJANGO_WEBHOOK || 'http://localhost:8000/ai-agent/bridge/incoming/';

const app = express();
app.use(express.json());

let client = null;
let currentQr = null;
let connectionStatus = 'disconnected';

function createClient() {
  client = new Client({
    authStrategy: new LocalAuth({ clientId: 'crm-bridge' }),
    puppeteer: { headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] },
  });

  client.on('qr', async (qr) => {
    currentQr = qr;
    connectionStatus = 'scanning';
    console.log('QR code generated');
  });

  client.on('ready', () => {
    currentQr = null;
    connectionStatus = 'connected';
    console.log('WhatsApp client is ready!');
  });

  client.on('disconnected', (reason) => {
    currentQr = null;
    connectionStatus = 'disconnected';
    console.log('WhatsApp client disconnected:', reason);
    setTimeout(() => {
      console.log('Attempting reconnect...');
      createClient();
      client.initialize();
    }, 5000);
  });

  client.on('message', async (msg) => {
    if (msg.fromMe) return;
    try {
      await fetch(DJANGO_WEBHOOK, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: msg.from.replace('@c.us', ''),
          message_body: msg.body,
          sender_name: msg._data.notifyName || '',
          whatsapp_message_id: msg.id._serialized,
          msg_type: 'text',
        }),
      });
    } catch (e) {
      console.error('Failed to forward message to Django:', e.message);
    }
  });

  client.on('message_ack', (msg, ack) => {
    // optional: track delivery status
  });
}

createClient();
client.initialize();

app.get('/status', (req, res) => {
  res.json({
    status: connectionStatus,
    hasQr: !!currentQr,
  });
});

app.get('/qr', async (req, res) => {
  if (!currentQr) {
    return res.status(404).json({ error: 'No QR code available' });
  }
  try {
    const qrImage = await qrcode.toDataURL(currentQr);
    res.json({ qr: qrImage });
  } catch (e) {
    res.status(500).json({ error: 'Failed to generate QR image' });
  }
});

app.post('/send', async (req, res) => {
  const { to, message } = req.body;
  if (!to || !message) {
    return res.status(400).json({ error: 'to and message are required' });
  }
  if (connectionStatus !== 'connected') {
    return res.status(503).json({ error: 'WhatsApp not connected' });
  }
  try {
    const chatId = `${to}@c.us`;
    await client.sendMessage(chatId, message);
    res.json({ success: true });
  } catch (e) {
    console.error('Failed to send message:', e.message);
    res.status(500).json({ error: e.message });
  }
});

app.get('/health', (req, res) => {
  res.json({ ok: true, status: connectionStatus });
});

app.listen(PORT, '127.0.0.1', () => {
  console.log(`WhatsApp bridge listening on port ${PORT}`);
});
