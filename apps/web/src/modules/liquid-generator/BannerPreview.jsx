/**
 * BannerPreview -- Rendu visuel des templates Braze.
 * Supporte : bannieres (5 types), emails complets (iframe), push (mockup mobile), SMS (mockup bulle).
 *
 * Templates bannieres : hero_banner, product_card, countdown, cta_simple, testimonial
 * Templates email : welcome_email, abandoned_cart_email, loyalty_email, post_purchase_email, winback_email
 * Template push : push_notification
 * Template SMS : sms_message
 */
import { useRef, useEffect, useState } from "react";

/* ── Helper : determine la categorie depuis le nom du template ── */
function getCategory(template) {
  if (!template) return "banner";
  if (template.endsWith("_email")) return "email";
  if (template === "push_notification") return "push";
  if (template === "sms_message") return "sms";
  return "banner";
}

/* ── Email Preview (iframe sandbox) ── */
function EmailPreview({ liquidCode }) {
  const iframeRef = useRef(null);
  const [iframeHeight, setIframeHeight] = useState(800);

  useEffect(() => {
    if (!iframeRef.current || !liquidCode) return;
    const doc = iframeRef.current.contentDocument || iframeRef.current.contentWindow.document;
    doc.open();
    doc.write(liquidCode);
    doc.close();

    // Auto-resize iframe to content
    const timer = setTimeout(() => {
      try {
        const h = doc.documentElement.scrollHeight || doc.body.scrollHeight;
        if (h > 100) setIframeHeight(h + 40);
      } catch {
        /* cross-origin fallback */
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [liquidCode]);

  return (
    <div style={{ textAlign: "center" }}>
      <div
        style={{
          display: "inline-block",
          background: "#e2e8f0",
          borderRadius: 16,
          padding: "12px 12px 4px",
          maxWidth: 640,
          width: "100%",
        }}
      >
        {/* Browser chrome mockup */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            marginBottom: 8,
            paddingLeft: 8,
          }}
        >
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#fc5c65" }} />
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#fed330" }} />
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#26de81" }} />
          <span
            style={{
              flex: 1,
              marginLeft: 12,
              background: "#fff",
              borderRadius: 4,
              padding: "4px 12px",
              fontSize: "0.7rem",
              color: "#999",
              textAlign: "center",
            }}
          >
            Apercu email
          </span>
        </div>
        <iframe
          ref={iframeRef}
          title="Email Preview"
          sandbox="allow-same-origin"
          style={{
            width: "100%",
            height: iframeHeight,
            border: "none",
            borderRadius: "0 0 8px 8px",
            background: "#fff",
          }}
        />
      </div>
    </div>
  );
}

/* ── Push Notification Mockup ── */
function PushPreview({ data }) {
  const p = data.params || {};
  const title = p.title || p.headline || "Notification";
  const body = p.body || p.subheadline || "Message de la notification";
  const imageUrl = p.image_url || null;
  const buttons = [];
  if (p.action_button_1_text) buttons.push(p.action_button_1_text);
  if (p.action_button_2_text) buttons.push(p.action_button_2_text);

  return (
    <div style={{ textAlign: "center" }}>
      {/* Phone mockup */}
      <div
        style={{
          display: "inline-block",
          width: 320,
          background: "linear-gradient(180deg, #1a1a2e 0%, #16213e 100%)",
          borderRadius: 36,
          padding: "48px 16px 32px",
          position: "relative",
          boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
        }}
      >
        {/* Notch */}
        <div
          style={{
            position: "absolute",
            top: 12,
            left: "50%",
            transform: "translateX(-50%)",
            width: 120,
            height: 24,
            background: "#000",
            borderRadius: 12,
          }}
        />

        {/* Time */}
        <div
          style={{
            color: "#fff",
            fontSize: 42,
            fontWeight: 300,
            textAlign: "center",
            marginBottom: 4,
            letterSpacing: 2,
          }}
        >
          09:41
        </div>
        <div
          style={{
            color: "rgba(255,255,255,0.6)",
            fontSize: 14,
            textAlign: "center",
            marginBottom: 32,
          }}
        >
          Lundi 24 mars
        </div>

        {/* Notification card */}
        <div
          style={{
            background: "rgba(255,255,255,0.95)",
            borderRadius: 16,
            overflow: "hidden",
            textAlign: "left",
            backdropFilter: "blur(20px)",
          }}
        >
          {/* App header */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "10px 14px 6px",
            }}
          >
            <div
              style={{
                width: 20,
                height: 20,
                borderRadius: 5,
                background: "linear-gradient(135deg, #e94560, #f00a0a)",
                flexShrink: 0,
              }}
            />
            <span style={{ fontSize: 12, color: "#999", fontWeight: 500 }}>MON APP</span>
            <span style={{ fontSize: 11, color: "#bbb", marginLeft: "auto" }}>maintenant</span>
          </div>

          {/* Content */}
          <div style={{ padding: "2px 14px 12px" }}>
            <div style={{ fontWeight: 700, fontSize: 14, color: "#1a1a2e", marginBottom: 2 }}>
              {title}
            </div>
            <div style={{ fontSize: 13, color: "#555", lineHeight: 1.4 }}>
              {body}
            </div>
          </div>

          {/* Image */}
          {imageUrl && (
            <div style={{ padding: "0 14px 12px" }}>
              <img
                src={imageUrl}
                alt="Push"
                style={{ width: "100%", borderRadius: 8, display: "block" }}
                onError={(e) => { e.target.style.display = "none"; }}
              />
            </div>
          )}

          {/* Action buttons */}
          {buttons.length > 0 && (
            <div style={{ borderTop: "1px solid #eee", display: "flex" }}>
              {buttons.map((btn, idx) => (
                <div
                  key={idx}
                  style={{
                    flex: 1,
                    textAlign: "center",
                    padding: "10px 8px",
                    fontSize: 13,
                    fontWeight: 600,
                    color: "#007AFF",
                    borderRight: idx < buttons.length - 1 ? "1px solid #eee" : "none",
                  }}
                >
                  {btn}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Home indicator */}
        <div
          style={{
            width: 100,
            height: 4,
            background: "rgba(255,255,255,0.3)",
            borderRadius: 2,
            margin: "24px auto 0",
          }}
        />
      </div>
    </div>
  );
}

/* ── SMS Mockup ── */
function SmsPreview({ data }) {
  const p = data.params || {};
  const messageText = p.message_text || data.liquid_code || "Votre message SMS ici";

  return (
    <div style={{ textAlign: "center" }}>
      {/* Phone mockup */}
      <div
        style={{
          display: "inline-block",
          width: 320,
          background: "#f2f2f7",
          borderRadius: 36,
          padding: "48px 16px 32px",
          position: "relative",
          boxShadow: "0 20px 60px rgba(0,0,0,0.15)",
          border: "3px solid #d1d1d6",
        }}
      >
        {/* Notch */}
        <div
          style={{
            position: "absolute",
            top: 12,
            left: "50%",
            transform: "translateX(-50%)",
            width: 120,
            height: 24,
            background: "#d1d1d6",
            borderRadius: 12,
          }}
        />

        {/* Messages header */}
        <div
          style={{
            textAlign: "center",
            marginBottom: 16,
            paddingBottom: 12,
            borderBottom: "1px solid #d1d1d6",
          }}
        >
          <div style={{ fontSize: 11, color: "#999", marginBottom: 2 }}>Messages</div>
          <div style={{ fontWeight: 700, fontSize: 16, color: "#1a1a2e" }}>Service Client</div>
          <div style={{ fontSize: 11, color: "#007AFF" }}>SMS</div>
        </div>

        {/* Date chip */}
        <div style={{ textAlign: "center", marginBottom: 16 }}>
          <span
            style={{
              fontSize: 11,
              color: "#999",
              background: "rgba(0,0,0,0.04)",
              padding: "3px 10px",
              borderRadius: 10,
            }}
          >
            Aujourd'hui 09:41
          </span>
        </div>

        {/* SMS bubble */}
        <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 16 }}>
          <div
            style={{
              background: "#e5e5ea",
              borderRadius: "18px 18px 18px 4px",
              padding: "10px 16px",
              maxWidth: "85%",
              fontSize: 14,
              color: "#1a1a2e",
              lineHeight: 1.45,
              wordBreak: "break-word",
            }}
          >
            {messageText}
          </div>
        </div>

        {/* Character count */}
        <div
          style={{
            textAlign: "center",
            fontSize: 11,
            color: messageText.length > 160 ? "#e17055" : "#999",
            fontWeight: messageText.length > 160 ? 600 : 400,
          }}
        >
          {messageText.length} / 160 caracteres
          {messageText.length > 160 && " (depassement)"}
        </div>

        {/* Input bar */}
        <div
          style={{
            marginTop: 16,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <div
            style={{
              flex: 1,
              background: "#fff",
              borderRadius: 20,
              border: "1px solid #d1d1d6",
              padding: "8px 16px",
              fontSize: 13,
              color: "#999",
            }}
          >
            Message texte
          </div>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: "50%",
              background: "#007AFF",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#fff",
              fontSize: 16,
              fontWeight: 700,
              flexShrink: 0,
            }}
          >
            &#x2191;
          </div>
        </div>

        {/* Home indicator */}
        <div
          style={{
            width: 100,
            height: 4,
            background: "rgba(0,0,0,0.15)",
            borderRadius: 2,
            margin: "16px auto 0",
          }}
        />
      </div>
    </div>
  );
}

/* ── Composant principal ── */
export default function BannerPreview({ data }) {
  if (!data) return null;

  const category = getCategory(data.template);

  /* ── Email templates ── */
  if (category === "email") {
    const code = data.liquid_code || data.html_skeleton || "<!-- Pas de code email genere -->";
    return <EmailPreview liquidCode={code} />;
  }

  /* ── Push notification ── */
  if (category === "push") {
    return <PushPreview data={data} />;
  }

  /* ── SMS ── */
  if (category === "sms") {
    return <SmsPreview data={data} />;
  }

  /* ── Banner templates (existing) ── */
  const p = data.params || {};
  const bgColor = p.bg_color || "#040066";
  const textColor = p.text_color || "#ffffff";
  const ctaColor = p.cta_color || "#f00a0a";

  /* ── Testimonial ── */
  if (data.template === "testimonial") {
    return (
      <div
        style={{
          background: bgColor,
          color: textColor,
          borderRadius: 12,
          padding: "40px 32px",
          textAlign: "center",
          position: "relative",
        }}
      >
        <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.3 }}>&quot;</div>
        <p
          style={{
            fontSize: 18,
            lineHeight: 1.6,
            fontStyle: "italic",
            maxWidth: 500,
            margin: "0 auto 20px",
          }}
        >
          {p.quote || "Citation client"}
        </p>
        <p style={{ fontWeight: 700, fontSize: 14 }}>
          {p.author || "Client"} —{" "}
          <span style={{ opacity: 0.7 }}>{p.role || ""}</span>
        </p>
        {p.cta_text && (
          <div
            style={{
              display: "inline-block",
              marginTop: 20,
              background: ctaColor,
              color: "#fff",
              padding: "10px 28px",
              borderRadius: 6,
              fontWeight: 600,
              fontSize: 14,
            }}
          >
            {p.cta_text}
          </div>
        )}
      </div>
    );
  }

  /* ── Product Card ── */
  if (data.template === "product_card") {
    return (
      <div
        style={{
          background: bgColor,
          color: textColor,
          borderRadius: 12,
          padding: 32,
          display: "flex",
          alignItems: "center",
          gap: 24,
        }}
      >
        <div
          style={{
            width: 120,
            height: 120,
            background: "rgba(0,0,0,0.06)",
            borderRadius: 12,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 40,
            flexShrink: 0,
          }}
        >
          {"\uD83D\uDECD\uFE0F"}
        </div>
        <div style={{ flex: 1 }}>
          {p.badge && (
            <span
              style={{
                background: ctaColor,
                color: "#fff",
                padding: "3px 10px",
                borderRadius: 4,
                fontSize: 11,
                fontWeight: 700,
                textTransform: "uppercase",
              }}
            >
              {p.badge}
            </span>
          )}
          <h2
            style={{
              fontSize: 22,
              fontWeight: 700,
              margin: "8px 0 4px",
              lineHeight: 1.2,
            }}
          >
            {p.product_name || p.headline || "Produit"}
          </h2>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginBottom: 12,
            }}
          >
            {p.old_price && (
              <span
                style={{
                  textDecoration: "line-through",
                  opacity: 0.5,
                  fontSize: 16,
                }}
              >
                {p.old_price}
              </span>
            )}
            {p.price && (
              <span style={{ fontSize: 24, fontWeight: 700, color: ctaColor }}>
                {p.price}
              </span>
            )}
          </div>
          {p.cta_text && (
            <div
              style={{
                display: "inline-block",
                background: ctaColor,
                color: "#222",
                padding: "10px 24px",
                borderRadius: 6,
                fontWeight: 600,
                fontSize: 14,
              }}
            >
              {p.cta_text}
            </div>
          )}
        </div>
      </div>
    );
  }

  /* ── Countdown ── */
  if (data.template === "countdown") {
    return (
      <div
        style={{
          background: `linear-gradient(135deg, ${bgColor}, ${ctaColor}44)`,
          color: textColor,
          borderRadius: 12,
          padding: "40px 32px",
          textAlign: "center",
        }}
      >
        <h2
          style={{
            fontSize: 26,
            fontWeight: 800,
            marginBottom: 16,
            lineHeight: 1.2,
          }}
        >
          {p.headline || "Offre limitee"}
        </h2>
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 12,
            marginBottom: 24,
          }}
        >
          {["12", "04", "32", "15"].map((v, i) => (
            <div
              key={i}
              style={{
                background: "rgba(0,0,0,0.08)",
                borderRadius: 8,
                padding: "12px 16px",
                minWidth: 56,
              }}
            >
              <div style={{ fontSize: 28, fontWeight: 800 }}>{v}</div>
              <div
                style={{
                  fontSize: 10,
                  opacity: 0.7,
                  textTransform: "uppercase",
                }}
              >
                {["jours", "heures", "min", "sec"][i]}
              </div>
            </div>
          ))}
        </div>
        {p.cta_text && (
          <div
            style={{
              display: "inline-block",
              background: ctaColor,
              color: "#fff",
              padding: "12px 32px",
              borderRadius: 6,
              fontWeight: 700,
              fontSize: 15,
            }}
          >
            {p.cta_text}
          </div>
        )}
      </div>
    );
  }

  /* ── CTA Simple ── */
  if (data.template === "cta_simple") {
    return (
      <div
        style={{
          background: bgColor,
          color: textColor,
          borderRadius: 12,
          padding: "32px 28px",
          textAlign: "center",
        }}
      >
        <h2
          style={{
            fontSize: 22,
            fontWeight: 700,
            marginBottom: 16,
            lineHeight: 1.3,
          }}
        >
          {p.headline || "Call to action"}
        </h2>
        {p.cta_text && (
          <div
            style={{
              display: "inline-block",
              background: ctaColor,
              color: "#fff",
              padding: "12px 32px",
              borderRadius: 6,
              fontWeight: 700,
              fontSize: 15,
            }}
          >
            {p.cta_text}
          </div>
        )}
      </div>
    );
  }

  /* ── Hero Banner (default) ── */
  return (
    <div
      style={{
        background: `linear-gradient(135deg, ${bgColor} 0%, ${bgColor}dd 100%)`,
        color: textColor,
        borderRadius: 12,
        padding: "48px 32px",
        textAlign: "center",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: -40,
          right: -40,
          width: 200,
          height: 200,
          background: ctaColor,
          opacity: 0.08,
          borderRadius: "50%",
        }}
      />
      <h1
        style={{
          fontSize: 28,
          fontWeight: 800,
          marginBottom: 12,
          lineHeight: 1.2,
          position: "relative",
        }}
      >
        {p.headline || "Headline"}
      </h1>
      {p.subheadline && (
        <p
          style={{
            fontSize: 16,
            opacity: 0.85,
            maxWidth: 480,
            margin: "0 auto 24px",
            lineHeight: 1.5,
            position: "relative",
          }}
        >
          {p.subheadline}
        </p>
      )}
      {p.cta_text && (
        <div
          style={{
            display: "inline-block",
            background: ctaColor,
            color: "#222",
            padding: "12px 32px",
            borderRadius: 6,
            fontWeight: 700,
            fontSize: 15,
            position: "relative",
          }}
        >
          {p.cta_text}
        </div>
      )}
    </div>
  );
}
