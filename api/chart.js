module.exports = async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  const sym = (req.query.sym || "BTC").toUpperCase();
  const pairMap = {
    USDT: "BTC_USDT",
    SILVER: "XAUT_USDT",
    HG1: "BTC_USDT",
    USOIL: "BTC_USDT"
  };
  const pair = pairMap[sym] || `${sym}_USDT`;

  try {
    const r = await fetch(`https://gateio.ws{pair}&interval=15m&limit=70`);
    const rows = await r.json();
    if (!Array.isArray(rows)) throw new Error("Invalid response");

    const formatted = rows.map(c => ({
      time: Number(c.at(0)),
      open: parseFloat(c.at(5)),
      high: parseFloat(c.at(3)),
      low: parseFloat(c.at(4)),
      close: parseFloat(c.at(2))
    }));

    return res.status(200).json({ Data: { Data: formatted } });
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
};
