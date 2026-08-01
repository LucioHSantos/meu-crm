import express from 'express';
import qrcode from 'qrcode';
import pkg from 'whatsapp-web.js';
const { Client, LocalAuth } = pkg;

const PORT = process.env.BRIDGE_PORT || 3001;
const DJANGO_WEBHOOK = process.env.DJANGO_WEBHOOK || 'http://localhost:8000/ai-agent/bridge/incoming/';
const SEND_TIMEOUT = 30000;

const app = express();
app.use(express.json());

let client = null;
let currentQr = null;
let connectionStatus = 'disconnected';

function timeout(ms) {
  return new Promise((_, reject) => setTimeout(() => reject(new Error('TIMEOUT')), ms));
}

function createClient() {
    client = new Client({
    authStrategy: new LocalAuth({ clientId: 'crm-bridge' }),
    puppeteer: {
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
    },
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
    console.log('Message received from:', msg.from, 'body:', msg.body.slice(0, 100));
    try {
      const resp = await fetch(DJANGO_WEBHOOK, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Forwarded-Proto': 'https',
        },
        body: JSON.stringify({
          phone_number: msg.from,
          message_body: msg.body,
          sender_name: msg._data.notifyName || '',
          whatsapp_message_id: msg.id._serialized,
          msg_type: 'text',
        }),
      });
      if (!resp.ok) {
        console.error('Django webhook returned', resp.status);
      }
    } catch (e) {
      console.error('Failed to forward message to Django:', e.message);
    }
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
  let { to, message } = req.body;
  if (!to || !message) {
    return res.status(400).json({ error: 'to and message are required' });
  }
  if (connectionStatus !== 'connected') {
    return res.status(503).json({ error: 'WhatsApp not connected' });
  }
  try {
    const chatId = to.includes('@') ? to : `${to}@c.us`;
    console.log('Sending to:', chatId);
    await Promise.race([
      client.sendMessage(chatId, message),
      timeout(SEND_TIMEOUT),
    ]);
    console.log('Send OK to:', chatId);
    res.json({ success: true });
  } catch (e) {
    if (e.message === 'TIMEOUT') {
      console.error('Send TIMEOUT to:', to);
    } else {
      console.error('Failed to send message:', e.message);
    }
    console.log('Reloading page after send failure...');
    try {
      if (client && client.pupPage) {
        await client.pupPage.reload({ waitUntil: 'networkidle0' });
        await new Promise(r => setTimeout(r, 5000));
        connectionStatus = 'connected';
        console.log('Page reloaded');
      }
    } catch (reloadErr) {
      console.error('Page reload failed:', reloadErr.message);
    }
    res.status(500).json({ error: e.message || 'Send timeout' });
  }
});

app.get('/health', (req, res) => {
  res.json({ ok: true, status: connectionStatus });
});

app.listen(PORT, '127.0.0.1', () => {
  console.log(`WhatsApp bridge listening on port ${PORT}`);
});
