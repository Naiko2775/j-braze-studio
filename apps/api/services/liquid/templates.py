"""Templates predefinies pour le Liquid Generator.

Porte les 5 templates depuis braze/src/App.jsx (TEMPLATES + EXAMPLE_BRIEFS)
avec enrichissement : champs attendus (structure) et exemples de brief.

Categories :
- banner : bannieres HTML simples (hero, product card, countdown, etc.)
- email  : emails complets multi-blocs (welcome, abandoned cart, loyalty, etc.)
- push   : notifications push mobiles
- sms    : messages SMS courts
"""

from __future__ import annotations

from typing import Any


TEMPLATES: dict[str, dict[str, Any]] = {
    # =========================================================================
    # BANNER TEMPLATES (existants)
    # =========================================================================
    "hero_banner": {
        "name": "Hero Banner",
        "description": "Grande banniere promotionnelle plein ecran",
        "icon": "hero",
        "category": "banner",
        "structure": {
            "required": ["headline", "cta_text", "cta_url"],
            "optional": [
                "subheadline",
                "image_url",
                "bg_color",
                "text_color",
                "cta_color",
            ],
        },
        "example_brief": (
            "Banniere soldes d'ete pour nos clients VIP, ton premium et exclusif, "
            "couleurs #040066 et #f00a0a, CTA vers /collection-ete"
        ),
    },
    "product_card": {
        "name": "Product Card",
        "description": "Mise en avant d'un produit specifique",
        "icon": "product",
        "category": "banner",
        "structure": {
            "required": ["product_name", "price", "cta_text", "cta_url"],
            "optional": [
                "old_price",
                "badge",
                "headline",
                "image_url",
                "bg_color",
                "text_color",
                "cta_color",
            ],
        },
        "example_brief": (
            "Promo flash -30% sur les sneakers, segment jeunes 18-25, "
            "ton dynamique et fun, urgence 48h"
        ),
    },
    "countdown": {
        "name": "Countdown",
        "description": "Offre limitee avec urgence",
        "icon": "countdown",
        "category": "banner",
        "structure": {
            "required": ["headline", "end_date", "cta_text", "cta_url"],
            "optional": [
                "subheadline",
                "bg_color",
                "text_color",
                "cta_color",
            ],
        },
        "example_brief": (
            "Vente flash 48h sur toute la collection hiver, "
            "ton urgent, CTA vers /vente-flash, date de fin demain 23h59"
        ),
    },
    "cta_simple": {
        "name": "CTA Simple",
        "description": "Banniere minimaliste avec call-to-action",
        "icon": "cta",
        "category": "banner",
        "structure": {
            "required": ["headline", "cta_text", "cta_url"],
            "optional": [
                "bg_color",
                "text_color",
                "cta_color",
            ],
        },
        "example_brief": (
            "Bienvenue aux nouveaux inscrits, ton chaleureux, "
            "avec prenom personnalise, CTA vers l'onboarding"
        ),
    },
    "testimonial": {
        "name": "Testimonial",
        "description": "Social proof / avis client",
        "icon": "testimonial",
        "category": "banner",
        "structure": {
            "required": ["quote", "author", "cta_text", "cta_url"],
            "optional": [
                "role",
                "headline",
                "bg_color",
                "text_color",
                "cta_color",
            ],
        },
        "example_brief": (
            "Banniere testimonial client satisfait pour notre assurance auto, "
            "ton rassurant et professionnel"
        ),
    },

    # =========================================================================
    # EMAIL TEMPLATES (complets multi-blocs)
    # =========================================================================
    "welcome_email": {
        "name": "Welcome Email",
        "description": "Email de bienvenue avec avantages et onboarding",
        "icon": "welcome",
        "category": "email",
        "structure": {
            "required": ["headline", "welcome_message", "cta_text", "cta_url"],
            "optional": [
                "logo_url",
                "hero_image_url",
                "advantages",
                "bg_color",
                "text_color",
                "cta_color",
                "footer_text",
            ],
        },
        "example_brief": (
            "Email de bienvenue pour nouveaux inscrits e-commerce mode, "
            "ton chaleureux, 3 avantages (livraison gratuite, retours 30j, programme fidelite), "
            "CTA vers /mon-compte, couleurs #1a1a2e et #e94560"
        ),
        "html_skeleton": (
            '<!DOCTYPE html>\n'
            '<html lang="fr">\n'
            '<head>\n'
            '  <meta charset="utf-8">\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '  <title>Bienvenue</title>\n'
            '  <style>\n'
            '    @media only screen and (max-width: 600px) {\n'
            '      .container { width: 100% !important; }\n'
            '      .hero-img { height: 150px !important; }\n'
            '      .advantage-cell { display: block !important; width: 100% !important; }\n'
            '    }\n'
            '  </style>\n'
            '</head>\n'
            '<body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">\n'
            '  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f7;">\n'
            '    <tr><td align="center" style="padding:20px 0;">\n'
            '      <table role="presentation" class="container" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:8px;overflow:hidden;">\n'
            '        <!-- Logo Header -->\n'
            '        <tr><td align="center" style="padding:30px 40px 20px;background-color:#1a1a2e;">\n'
            '          <img src="{{ message_extras.${logo_url} | default: \'https://via.placeholder.com/150x50/1a1a2e/ffffff?text=LOGO\' }}" alt="Logo" width="150" style="display:block;" />\n'
            '        </td></tr>\n'
            '        <!-- Hero Banner -->\n'
            '        <tr><td style="background-color:#1a1a2e;">\n'
            '          <img src="{{ message_extras.${hero_image_url} | default: \'https://via.placeholder.com/600x200/e94560/ffffff?text=Bienvenue\' }}" alt="Hero" width="600" class="hero-img" style="display:block;width:100%;height:auto;" />\n'
            '        </td></tr>\n'
            '        <!-- Welcome Message -->\n'
            '        <tr><td style="padding:40px 40px 20px;text-align:center;">\n'
            '          <h1 style="margin:0 0 16px;font-size:28px;color:#1a1a2e;font-weight:800;">\n'
            '            Bienvenue {{ ${first_name} | default: \'cher client\' }} !\n'
            '          </h1>\n'
            '          {% if custom_attribute.${gender} == \'F\' %}\n'
            '          <p style="margin:0;font-size:16px;color:#555;line-height:1.6;">Chere {{ ${first_name} | default: \'cliente\' }}, nous sommes ravis de vous accueillir.</p>\n'
            '          {% elsif custom_attribute.${gender} == \'M\' %}\n'
            '          <p style="margin:0;font-size:16px;color:#555;line-height:1.6;">Cher {{ ${first_name} | default: \'client\' }}, nous sommes ravis de vous accueillir.</p>\n'
            '          {% else %}\n'
            '          <p style="margin:0;font-size:16px;color:#555;line-height:1.6;">Nous sommes ravis de vous accueillir parmi nous.</p>\n'
            '          {% endif %}\n'
            '        </td></tr>\n'
            '        <!-- 3 Advantages -->\n'
            '        <tr><td style="padding:0 40px 30px;">\n'
            '          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">\n'
            '            <tr>\n'
            '              <td class="advantage-cell" width="33%" style="padding:10px;text-align:center;vertical-align:top;">\n'
            '                <div style="font-size:32px;margin-bottom:8px;">&#x1F69A;</div>\n'
            '                <strong style="font-size:14px;color:#1a1a2e;">Livraison gratuite</strong>\n'
            '                <p style="font-size:12px;color:#777;margin:4px 0 0;">Des 49EUR d\'achat</p>\n'
            '              </td>\n'
            '              <td class="advantage-cell" width="33%" style="padding:10px;text-align:center;vertical-align:top;">\n'
            '                <div style="font-size:32px;margin-bottom:8px;">&#x1F504;</div>\n'
            '                <strong style="font-size:14px;color:#1a1a2e;">Retours 30 jours</strong>\n'
            '                <p style="font-size:12px;color:#777;margin:4px 0 0;">Satisfait ou rembourse</p>\n'
            '              </td>\n'
            '              <td class="advantage-cell" width="33%" style="padding:10px;text-align:center;vertical-align:top;">\n'
            '                <div style="font-size:32px;margin-bottom:8px;">&#x2B50;</div>\n'
            '                <strong style="font-size:14px;color:#1a1a2e;">Programme fidelite</strong>\n'
            '                <p style="font-size:12px;color:#777;margin:4px 0 0;">Cumulez des points</p>\n'
            '              </td>\n'
            '            </tr>\n'
            '          </table>\n'
            '        </td></tr>\n'
            '        <!-- CTA -->\n'
            '        <tr><td align="center" style="padding:0 40px 40px;">\n'
            '          <a href="{{ deep_link | default: \'/mon-compte\' }}" style="display:inline-block;background-color:#e94560;color:#ffffff;padding:14px 40px;border-radius:6px;font-weight:700;font-size:16px;text-decoration:none;">Decouvrir mon espace</a>\n'
            '        </td></tr>\n'
            '        <!-- Footer -->\n'
            '        <tr><td style="padding:20px 40px;background-color:#f4f4f7;text-align:center;border-top:1px solid #eee;">\n'
            '          <p style="margin:0 0 8px;font-size:12px;color:#999;">Vous recevez cet email car vous etes inscrit(e) sur notre site.</p>\n'
            '          <a href="{{ subscription_management_url }}" style="font-size:12px;color:#999;text-decoration:underline;">Se desabonner</a>\n'
            '        </td></tr>\n'
            '      </table>\n'
            '    </td></tr>\n'
            '  </table>\n'
            '</body>\n'
            '</html>'
        ),
    },
    "abandoned_cart_email": {
        "name": "Abandoned Cart Email",
        "description": "Relance panier abandonne avec produits et recommandations",
        "icon": "cart",
        "category": "email",
        "structure": {
            "required": ["headline", "cta_text", "cta_url"],
            "optional": [
                "logo_url",
                "cart_items",
                "total_price",
                "recommendations",
                "bg_color",
                "text_color",
                "cta_color",
                "footer_text",
            ],
        },
        "example_brief": (
            "Email de relance panier abandonne pour e-commerce beaute, "
            "rappeler les produits laisses, afficher le total, "
            "proposer des recommandations, CTA 'Finaliser ma commande', ton amical et incitatif"
        ),
        "html_skeleton": (
            '<!DOCTYPE html>\n'
            '<html lang="fr">\n'
            '<head>\n'
            '  <meta charset="utf-8">\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '  <title>Votre panier vous attend</title>\n'
            '  <style>\n'
            '    @media only screen and (max-width: 600px) {\n'
            '      .container { width: 100% !important; }\n'
            '      .product-img { width: 60px !important; height: 60px !important; }\n'
            '    }\n'
            '  </style>\n'
            '</head>\n'
            '<body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">\n'
            '  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f7;">\n'
            '    <tr><td align="center" style="padding:20px 0;">\n'
            '      <table role="presentation" class="container" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:8px;overflow:hidden;">\n'
            '        <!-- Header -->\n'
            '        <tr><td align="center" style="padding:30px 40px;background-color:#2d3436;">\n'
            '          <img src="{{ message_extras.${logo_url} | default: \'https://via.placeholder.com/150x50/2d3436/ffffff?text=LOGO\' }}" alt="Logo" width="150" style="display:block;" />\n'
            '        </td></tr>\n'
            '        <!-- Reminder -->\n'
            '        <tr><td style="padding:40px 40px 20px;text-align:center;">\n'
            '          <div style="font-size:48px;margin-bottom:16px;">&#x1F6D2;</div>\n'
            '          <h1 style="margin:0 0 12px;font-size:24px;color:#2d3436;font-weight:800;">\n'
            '            {{ ${first_name} | default: \'Cher client\' }}, vous avez oublie quelque chose !\n'
            '          </h1>\n'
            '          <p style="margin:0;font-size:15px;color:#636e72;line-height:1.5;">Votre panier vous attend. Finalisez votre commande avant que vos articles ne soient plus disponibles.</p>\n'
            '        </td></tr>\n'
            '        <!-- Cart Items Loop -->\n'
            '        <tr><td style="padding:0 40px 20px;">\n'
            '          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #eee;border-radius:6px;">\n'
            '            <tr><td style="padding:16px;background-color:#fafafa;border-bottom:1px solid #eee;">\n'
            '              <strong style="font-size:14px;color:#2d3436;">Votre panier</strong>\n'
            '            </td></tr>\n'
            '            {% for item in ${cart_items} %}\n'
            '            <tr><td style="padding:12px 16px;border-bottom:1px solid #f0f0f0;">\n'
            '              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">\n'
            '                <tr>\n'
            '                  <td width="80" style="vertical-align:middle;">\n'
            '                    {% connected_content https://api.example.com/products/{{ item.product_id }}/image :save product_img %}\n'
            '                    <img src="{{ product_img.url | default: item.image_url }}" alt="{{ item.name }}" class="product-img" width="80" height="80" style="display:block;border-radius:4px;object-fit:cover;" />\n'
            '                  </td>\n'
            '                  <td style="vertical-align:middle;padding-left:12px;">\n'
            '                    <strong style="font-size:14px;color:#2d3436;">{{ item.name }}</strong>\n'
            '                    <p style="margin:4px 0 0;font-size:12px;color:#636e72;">Qte : {{ item.quantity | default: 1 }}</p>\n'
            '                  </td>\n'
            '                  <td width="80" style="vertical-align:middle;text-align:right;">\n'
            '                    <strong style="font-size:15px;color:#2d3436;">{{ item.price }}EUR</strong>\n'
            '                  </td>\n'
            '                </tr>\n'
            '              </table>\n'
            '            </td></tr>\n'
            '            {% endfor %}\n'
            '            <tr><td style="padding:16px;text-align:right;background-color:#fafafa;">\n'
            '              <strong style="font-size:16px;color:#2d3436;">Total : {{ custom_attribute.${cart_total} | default: \'--\' }}EUR</strong>\n'
            '            </td></tr>\n'
            '          </table>\n'
            '        </td></tr>\n'
            '        <!-- CTA -->\n'
            '        <tr><td align="center" style="padding:10px 40px 30px;">\n'
            '          <a href="{{ deep_link | default: \'/checkout\' }}" style="display:inline-block;background-color:#e17055;color:#ffffff;padding:14px 40px;border-radius:6px;font-weight:700;font-size:16px;text-decoration:none;">Finaliser ma commande</a>\n'
            '        </td></tr>\n'
            '        <!-- Recommendations -->\n'
            '        <tr><td style="padding:0 40px 30px;">\n'
            '          <p style="margin:0 0 12px;font-size:14px;color:#2d3436;font-weight:700;">Vous aimerez aussi</p>\n'
            '          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">\n'
            '            <tr>\n'
            '              {% for rec in ${recommendations} %}\n'
            '              <td width="33%" style="padding:0 6px;text-align:center;vertical-align:top;">\n'
            '                <img src="{{ rec.image_url }}" alt="{{ rec.name }}" width="150" style="display:block;width:100%;border-radius:4px;margin-bottom:8px;" />\n'
            '                <p style="margin:0;font-size:12px;color:#2d3436;font-weight:600;">{{ rec.name }}</p>\n'
            '                <p style="margin:2px 0 0;font-size:12px;color:#e17055;">{{ rec.price }}EUR</p>\n'
            '              </td>\n'
            '              {% endfor %}\n'
            '            </tr>\n'
            '          </table>\n'
            '        </td></tr>\n'
            '        <!-- Footer -->\n'
            '        <tr><td style="padding:20px 40px;background-color:#f4f4f7;text-align:center;border-top:1px solid #eee;">\n'
            '          <p style="margin:0 0 8px;font-size:12px;color:#999;">Besoin d\'aide ? Contactez-nous a support@example.com</p>\n'
            '          <a href="{{ subscription_management_url }}" style="font-size:12px;color:#999;text-decoration:underline;">Se desabonner</a>\n'
            '        </td></tr>\n'
            '      </table>\n'
            '    </td></tr>\n'
            '  </table>\n'
            '</body>\n'
            '</html>'
        ),
    },
    "loyalty_email": {
        "name": "Loyalty Program Email",
        "description": "Email fidelite avec statut, points et avantages exclusifs",
        "icon": "loyalty",
        "category": "email",
        "structure": {
            "required": ["headline", "cta_text", "cta_url"],
            "optional": [
                "logo_url",
                "loyalty_tier",
                "current_points",
                "next_tier_points",
                "advantages",
                "bg_color",
                "text_color",
                "cta_color",
                "footer_text",
            ],
        },
        "example_brief": (
            "Email programme fidelite pour clients existants, afficher leur statut "
            "(Bronze/Silver/Gold), points actuels et prochain palier, "
            "avantages exclusifs du palier, CTA vers /fidelite, ton valorisant et exclusif"
        ),
        "html_skeleton": (
            '<!DOCTYPE html>\n'
            '<html lang="fr">\n'
            '<head>\n'
            '  <meta charset="utf-8">\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '  <title>Votre fidelite recompensee</title>\n'
            '  <style>\n'
            '    @media only screen and (max-width: 600px) {\n'
            '      .container { width: 100% !important; }\n'
            '      .advantage-cell { display: block !important; width: 100% !important; }\n'
            '    }\n'
            '  </style>\n'
            '</head>\n'
            '<body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">\n'
            '  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f7;">\n'
            '    <tr><td align="center" style="padding:20px 0;">\n'
            '      <table role="presentation" class="container" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:8px;overflow:hidden;">\n'
            '        <!-- Header -->\n'
            '        <tr><td align="center" style="padding:30px 40px;background-color:#0c0c1d;">\n'
            '          <img src="{{ message_extras.${logo_url} | default: \'https://via.placeholder.com/150x50/0c0c1d/ffffff?text=LOGO\' }}" alt="Logo" width="150" style="display:block;" />\n'
            '        </td></tr>\n'
            '        <!-- Loyalty Status -->\n'
            '        <tr><td style="padding:40px 40px 20px;text-align:center;">\n'
            '          {% if custom_attribute.${loyalty_tier} == \'Gold\' %}\n'
            '          <div style="display:inline-block;background:linear-gradient(135deg,#f7d794,#f19066);color:#6c3502;padding:8px 24px;border-radius:20px;font-size:14px;font-weight:700;margin-bottom:16px;">&#x1F451; Membre Gold</div>\n'
            '          {% elsif custom_attribute.${loyalty_tier} == \'Silver\' %}\n'
            '          <div style="display:inline-block;background:linear-gradient(135deg,#dfe6e9,#b2bec3);color:#2d3436;padding:8px 24px;border-radius:20px;font-size:14px;font-weight:700;margin-bottom:16px;">&#x2B50; Membre Silver</div>\n'
            '          {% else %}\n'
            '          <div style="display:inline-block;background:linear-gradient(135deg,#fab1a0,#e17055);color:#6c3502;padding:8px 24px;border-radius:20px;font-size:14px;font-weight:700;margin-bottom:16px;">&#x1F3C5; Membre Bronze</div>\n'
            '          {% endif %}\n'
            '          <h1 style="margin:16px 0 12px;font-size:26px;color:#0c0c1d;font-weight:800;">\n'
            '            Felicitations {{ ${first_name} | default: \'cher membre\' }} !\n'
            '          </h1>\n'
            '          <p style="margin:0;font-size:15px;color:#636e72;line-height:1.5;">Votre fidelite est precieuse. Voici votre recapitulatif.</p>\n'
            '        </td></tr>\n'
            '        <!-- Points Progress Bar -->\n'
            '        <tr><td style="padding:0 40px 30px;">\n'
            '          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f8f9fa;border-radius:8px;padding:20px;">\n'
            '            <tr><td style="padding:20px;">\n'
            '              <p style="margin:0 0 8px;font-size:14px;color:#636e72;">Vos points fidelite</p>\n'
            '              <p style="margin:0 0 12px;font-size:32px;font-weight:800;color:#0c0c1d;">{{ custom_attribute.${loyalty_points} | default: \'0\' }} pts</p>\n'
            '              <!-- Progress bar -->\n'
            '              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">\n'
            '                <tr><td style="background-color:#dfe6e9;border-radius:10px;height:12px;">\n'
            '                  <div style="background:linear-gradient(90deg,#e94560,#f7d794);border-radius:10px;height:12px;width:{{ custom_attribute.${loyalty_progress} | default: \'45\' }}%;"></div>\n'
            '                </td></tr>\n'
            '              </table>\n'
            '              <p style="margin:8px 0 0;font-size:12px;color:#999;">\n'
            '                {% if custom_attribute.${loyalty_tier} == \'Gold\' %}\n'
            '                Vous etes au palier maximum !\n'
            '                {% else %}\n'
            '                Plus que {{ custom_attribute.${points_to_next_tier} | default: \'500\' }} pts pour le palier suivant\n'
            '                {% endif %}\n'
            '              </p>\n'
            '            </td></tr>\n'
            '          </table>\n'
            '        </td></tr>\n'
            '        <!-- Exclusive Advantages -->\n'
            '        <tr><td style="padding:0 40px 30px;">\n'
            '          <h2 style="margin:0 0 16px;font-size:18px;color:#0c0c1d;font-weight:700;">Vos avantages exclusifs</h2>\n'
            '          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">\n'
            '            <tr>\n'
            '              <td class="advantage-cell" width="33%" style="padding:8px;text-align:center;vertical-align:top;">\n'
            '                <div style="background-color:#f8f9fa;border-radius:8px;padding:16px;">\n'
            '                  <div style="font-size:28px;margin-bottom:8px;">&#x1F381;</div>\n'
            '                  <strong style="font-size:13px;color:#0c0c1d;">Offre anniversaire</strong>\n'
            '                </div>\n'
            '              </td>\n'
            '              <td class="advantage-cell" width="33%" style="padding:8px;text-align:center;vertical-align:top;">\n'
            '                <div style="background-color:#f8f9fa;border-radius:8px;padding:16px;">\n'
            '                  <div style="font-size:28px;margin-bottom:8px;">&#x1F69A;</div>\n'
            '                  <strong style="font-size:13px;color:#0c0c1d;">Livraison offerte</strong>\n'
            '                </div>\n'
            '              </td>\n'
            '              <td class="advantage-cell" width="33%" style="padding:8px;text-align:center;vertical-align:top;">\n'
            '                <div style="background-color:#f8f9fa;border-radius:8px;padding:16px;">\n'
            '                  <div style="font-size:28px;margin-bottom:8px;">&#x1F525;</div>\n'
            '                  <strong style="font-size:13px;color:#0c0c1d;">Ventes privees</strong>\n'
            '                </div>\n'
            '              </td>\n'
            '            </tr>\n'
            '          </table>\n'
            '        </td></tr>\n'
            '        <!-- CTA -->\n'
            '        <tr><td align="center" style="padding:0 40px 40px;">\n'
            '          <a href="{{ deep_link | default: \'/fidelite\' }}" style="display:inline-block;background-color:#e94560;color:#ffffff;padding:14px 40px;border-radius:6px;font-weight:700;font-size:16px;text-decoration:none;">Voir mes avantages</a>\n'
            '        </td></tr>\n'
            '        <!-- Footer -->\n'
            '        <tr><td style="padding:20px 40px;background-color:#f4f4f7;text-align:center;border-top:1px solid #eee;">\n'
            '          <p style="margin:0 0 8px;font-size:12px;color:#999;">Programme fidelite - Conditions sur notre site</p>\n'
            '          <a href="{{ subscription_management_url }}" style="font-size:12px;color:#999;text-decoration:underline;">Se desabonner</a>\n'
            '        </td></tr>\n'
            '      </table>\n'
            '    </td></tr>\n'
            '  </table>\n'
            '</body>\n'
            '</html>'
        ),
    },
    "post_purchase_email": {
        "name": "Post-Purchase Email",
        "description": "Confirmation commande avec cross-sell et enquete NPS",
        "icon": "purchase",
        "category": "email",
        "structure": {
            "required": ["headline", "order_number", "cta_text", "cta_url"],
            "optional": [
                "logo_url",
                "order_items",
                "order_total",
                "tracking_url",
                "cross_sell_items",
                "nps_url",
                "bg_color",
                "text_color",
                "cta_color",
                "footer_text",
            ],
        },
        "example_brief": (
            "Email post-achat pour confirmer la commande, "
            "recapitulatif des produits achetes, lien de suivi, "
            "section 'Vous aimerez aussi' avec cross-sell, lien enquete NPS, "
            "ton rassurant et professionnel"
        ),
        "html_skeleton": (
            '<!DOCTYPE html>\n'
            '<html lang="fr">\n'
            '<head>\n'
            '  <meta charset="utf-8">\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '  <title>Confirmation de commande</title>\n'
            '  <style>\n'
            '    @media only screen and (max-width: 600px) {\n'
            '      .container { width: 100% !important; }\n'
            '      .cross-sell-cell { display: block !important; width: 100% !important; }\n'
            '    }\n'
            '  </style>\n'
            '</head>\n'
            '<body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">\n'
            '  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f7;">\n'
            '    <tr><td align="center" style="padding:20px 0;">\n'
            '      <table role="presentation" class="container" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:8px;overflow:hidden;">\n'
            '        <!-- Header -->\n'
            '        <tr><td align="center" style="padding:30px 40px;background-color:#00b894;">\n'
            '          <img src="{{ message_extras.${logo_url} | default: \'https://via.placeholder.com/150x50/00b894/ffffff?text=LOGO\' }}" alt="Logo" width="150" style="display:block;" />\n'
            '        </td></tr>\n'
            '        <!-- Confirmation -->\n'
            '        <tr><td style="padding:40px 40px 20px;text-align:center;">\n'
            '          <div style="font-size:48px;margin-bottom:16px;">&#x2705;</div>\n'
            '          <h1 style="margin:0 0 12px;font-size:24px;color:#2d3436;font-weight:800;">Merci pour votre commande !</h1>\n'
            '          <p style="margin:0 0 8px;font-size:15px;color:#636e72;">{{ ${first_name} | default: \'Cher client\' }}, votre commande <strong>#{{ event_properties.${order_id} | default: \'000000\' }}</strong> est confirmee.</p>\n'
            '          <a href="{{ event_properties.${tracking_url} | default: \'#\' }}" style="font-size:14px;color:#00b894;text-decoration:underline;">Suivre ma livraison</a>\n'
            '        </td></tr>\n'
            '        <!-- Order Items -->\n'
            '        <tr><td style="padding:0 40px 20px;">\n'
            '          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #eee;border-radius:6px;">\n'
            '            <tr><td style="padding:16px;background-color:#fafafa;border-bottom:1px solid #eee;">\n'
            '              <strong style="font-size:14px;color:#2d3436;">Recapitulatif</strong>\n'
            '            </td></tr>\n'
            '            {% for item in event_properties.${order_items} %}\n'
            '            <tr><td style="padding:12px 16px;border-bottom:1px solid #f0f0f0;">\n'
            '              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">\n'
            '                <tr>\n'
            '                  <td width="60" style="vertical-align:middle;">\n'
            '                    <img src="{{ item.image_url }}" alt="{{ item.name }}" width="60" height="60" style="display:block;border-radius:4px;object-fit:cover;" />\n'
            '                  </td>\n'
            '                  <td style="vertical-align:middle;padding-left:12px;">\n'
            '                    <strong style="font-size:14px;color:#2d3436;">{{ item.name }}</strong>\n'
            '                    <p style="margin:4px 0 0;font-size:12px;color:#636e72;">x{{ item.quantity | default: 1 }}</p>\n'
            '                  </td>\n'
            '                  <td width="80" style="vertical-align:middle;text-align:right;">\n'
            '                    <strong style="font-size:14px;color:#2d3436;">{{ item.price }}EUR</strong>\n'
            '                  </td>\n'
            '                </tr>\n'
            '              </table>\n'
            '            </td></tr>\n'
            '            {% endfor %}\n'
            '            <tr><td style="padding:16px;text-align:right;background-color:#fafafa;">\n'
            '              <strong style="font-size:16px;color:#2d3436;">Total : {{ event_properties.${order_total} | default: \'--\' }}EUR</strong>\n'
            '            </td></tr>\n'
            '          </table>\n'
            '        </td></tr>\n'
            '        <!-- Cross-sell -->\n'
            '        <tr><td style="padding:10px 40px 30px;">\n'
            '          <h2 style="margin:0 0 16px;font-size:18px;color:#2d3436;font-weight:700;">Vous aimerez aussi</h2>\n'
            '          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">\n'
            '            <tr>\n'
            '              {% for rec in ${cross_sell_items} %}\n'
            '              <td class="cross-sell-cell" width="33%" style="padding:0 6px;text-align:center;vertical-align:top;">\n'
            '                <a href="{{ rec.url }}" style="text-decoration:none;">\n'
            '                  <img src="{{ rec.image_url }}" alt="{{ rec.name }}" width="150" style="display:block;width:100%;border-radius:4px;margin-bottom:8px;" />\n'
            '                  <p style="margin:0;font-size:12px;color:#2d3436;font-weight:600;">{{ rec.name }}</p>\n'
            '                  <p style="margin:2px 0 0;font-size:12px;color:#00b894;">{{ rec.price }}EUR</p>\n'
            '                </a>\n'
            '              </td>\n'
            '              {% endfor %}\n'
            '            </tr>\n'
            '          </table>\n'
            '        </td></tr>\n'
            '        <!-- NPS Survey -->\n'
            '        <tr><td style="padding:0 40px 30px;">\n'
            '          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0fff4;border-radius:8px;">\n'
            '            <tr><td style="padding:24px;text-align:center;">\n'
            '              <p style="margin:0 0 12px;font-size:15px;color:#2d3436;font-weight:600;">Votre avis compte !</p>\n'
            '              <p style="margin:0 0 16px;font-size:13px;color:#636e72;">Comment evalueriez-vous votre experience ?</p>\n'
            '              <a href="{{ event_properties.${nps_url} | default: \'/feedback\' }}" style="display:inline-block;background-color:#00b894;color:#ffffff;padding:10px 28px;border-radius:6px;font-weight:600;font-size:14px;text-decoration:none;">Donner mon avis</a>\n'
            '            </td></tr>\n'
            '          </table>\n'
            '        </td></tr>\n'
            '        <!-- Footer -->\n'
            '        <tr><td style="padding:20px 40px;background-color:#f4f4f7;text-align:center;border-top:1px solid #eee;">\n'
            '          <p style="margin:0 0 8px;font-size:12px;color:#999;">Merci de votre confiance !</p>\n'
            '          <a href="{{ subscription_management_url }}" style="font-size:12px;color:#999;text-decoration:underline;">Se desabonner</a>\n'
            '        </td></tr>\n'
            '      </table>\n'
            '    </td></tr>\n'
            '  </table>\n'
            '</body>\n'
            '</html>'
        ),
    },
    "winback_email": {
        "name": "Win-Back Email",
        "description": "Email de reconquete avec offre personnalisee et urgence",
        "icon": "winback",
        "category": "email",
        "structure": {
            "required": ["headline", "offer_code", "cta_text", "cta_url"],
            "optional": [
                "logo_url",
                "discount_percent",
                "offer_expiry",
                "best_sellers",
                "bg_color",
                "text_color",
                "cta_color",
                "footer_text",
            ],
        },
        "example_brief": (
            "Email win-back pour clients inactifs depuis 90+ jours, "
            "offre -20% avec code promo unique, best-sellers, "
            "compteur d'expiration de l'offre, ton amical 'vous nous manquez', "
            "CTA vers /offre-speciale"
        ),
        "html_skeleton": (
            '<!DOCTYPE html>\n'
            '<html lang="fr">\n'
            '<head>\n'
            '  <meta charset="utf-8">\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '  <title>Vous nous manquez</title>\n'
            '  <style>\n'
            '    @media only screen and (max-width: 600px) {\n'
            '      .container { width: 100% !important; }\n'
            '      .bestseller-cell { display: block !important; width: 100% !important; }\n'
            '    }\n'
            '  </style>\n'
            '</head>\n'
            '<body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">\n'
            '  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f7;">\n'
            '    <tr><td align="center" style="padding:20px 0;">\n'
            '      <table role="presentation" class="container" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:8px;overflow:hidden;">\n'
            '        <!-- Header -->\n'
            '        <tr><td align="center" style="padding:30px 40px;background-color:#6c5ce7;">\n'
            '          <img src="{{ message_extras.${logo_url} | default: \'https://via.placeholder.com/150x50/6c5ce7/ffffff?text=LOGO\' }}" alt="Logo" width="150" style="display:block;" />\n'
            '        </td></tr>\n'
            '        <!-- You miss us -->\n'
            '        <tr><td style="padding:40px 40px 20px;text-align:center;">\n'
            '          <div style="font-size:48px;margin-bottom:16px;">&#x1F49C;</div>\n'
            '          <h1 style="margin:0 0 12px;font-size:26px;color:#2d3436;font-weight:800;">\n'
            '            {{ ${first_name} | default: \'Cher client\' }}, vous nous manquez !\n'
            '          </h1>\n'
            '          {% assign days_since = custom_attribute.${last_purchase_date} | date: "%s" | minus: "now" | date: "%s" | divided_by: 86400 | abs %}\n'
            '          {% if days_since > 180 %}\n'
            '          <p style="margin:0;font-size:15px;color:#636e72;line-height:1.5;">Cela fait plus de 6 mois que nous ne vous avons pas vu. Nous avons une offre speciale pour vous !</p>\n'
            '          {% elsif days_since > 90 %}\n'
            '          <p style="margin:0;font-size:15px;color:#636e72;line-height:1.5;">Cela fait un moment ! Revenez decouvrir nos nouveautes avec une offre rien que pour vous.</p>\n'
            '          {% else %}\n'
            '          <p style="margin:0;font-size:15px;color:#636e72;line-height:1.5;">Nous avons prepare une offre speciale pour vous faire plaisir !</p>\n'
            '          {% endif %}\n'
            '        </td></tr>\n'
            '        <!-- Offer Box -->\n'
            '        <tr><td style="padding:0 40px 24px;">\n'
            '          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:linear-gradient(135deg,#6c5ce7,#a29bfe);border-radius:12px;">\n'
            '            <tr><td style="padding:32px;text-align:center;">\n'
            '              <p style="margin:0 0 8px;font-size:14px;color:#dfe6e9;text-transform:uppercase;letter-spacing:2px;font-weight:600;">Offre exclusive</p>\n'
            '              <p style="margin:0 0 12px;font-size:48px;color:#ffffff;font-weight:800;">-20%</p>\n'
            '              <p style="margin:0 0 16px;font-size:14px;color:#dfe6e9;">sur toute votre prochaine commande</p>\n'
            '              <div style="display:inline-block;background-color:#ffffff;color:#6c5ce7;padding:10px 24px;border-radius:6px;font-weight:800;font-size:18px;letter-spacing:2px;">\n'
            '                {{ event_properties.${promo_code} | default: \'COMEBACK20\' }}\n'
            '              </div>\n'
            '            </td></tr>\n'
            '          </table>\n'
            '        </td></tr>\n'
            '        <!-- Expiry countdown -->\n'
            '        <tr><td style="padding:0 40px 24px;text-align:center;">\n'
            '          <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto;">\n'
            '            <tr>\n'
            '              <td style="padding:0 8px;text-align:center;">\n'
            '                <div style="background-color:#f8f9fa;border-radius:8px;padding:12px 16px;min-width:50px;">\n'
            '                  <div style="font-size:24px;font-weight:800;color:#6c5ce7;">02</div>\n'
            '                  <div style="font-size:10px;color:#999;text-transform:uppercase;">jours</div>\n'
            '                </div>\n'
            '              </td>\n'
            '              <td style="padding:0 8px;text-align:center;">\n'
            '                <div style="background-color:#f8f9fa;border-radius:8px;padding:12px 16px;min-width:50px;">\n'
            '                  <div style="font-size:24px;font-weight:800;color:#6c5ce7;">23</div>\n'
            '                  <div style="font-size:10px;color:#999;text-transform:uppercase;">heures</div>\n'
            '                </div>\n'
            '              </td>\n'
            '              <td style="padding:0 8px;text-align:center;">\n'
            '                <div style="background-color:#f8f9fa;border-radius:8px;padding:12px 16px;min-width:50px;">\n'
            '                  <div style="font-size:24px;font-weight:800;color:#6c5ce7;">59</div>\n'
            '                  <div style="font-size:10px;color:#999;text-transform:uppercase;">min</div>\n'
            '                </div>\n'
            '              </td>\n'
            '            </tr>\n'
            '          </table>\n'
            '          <p style="margin:12px 0 0;font-size:13px;color:#e17055;font-weight:600;">Offre valable jusqu\'au {{ event_properties.${offer_expiry} | default: \'31/12/2026\' }}</p>\n'
            '        </td></tr>\n'
            '        <!-- CTA -->\n'
            '        <tr><td align="center" style="padding:0 40px 30px;">\n'
            '          <a href="{{ deep_link | default: \'/offre-speciale\' }}" style="display:inline-block;background-color:#6c5ce7;color:#ffffff;padding:14px 40px;border-radius:6px;font-weight:700;font-size:16px;text-decoration:none;">En profiter maintenant</a>\n'
            '        </td></tr>\n'
            '        <!-- Best sellers -->\n'
            '        <tr><td style="padding:0 40px 30px;">\n'
            '          <h2 style="margin:0 0 16px;font-size:18px;color:#2d3436;font-weight:700;">Nos best-sellers du moment</h2>\n'
            '          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">\n'
            '            <tr>\n'
            '              {% for product in ${best_sellers} %}\n'
            '              <td class="bestseller-cell" width="33%" style="padding:0 6px;text-align:center;vertical-align:top;">\n'
            '                <a href="{{ product.url }}" style="text-decoration:none;">\n'
            '                  <img src="{{ product.image_url }}" alt="{{ product.name }}" width="150" style="display:block;width:100%;border-radius:4px;margin-bottom:8px;" />\n'
            '                  <p style="margin:0;font-size:12px;color:#2d3436;font-weight:600;">{{ product.name }}</p>\n'
            '                  <p style="margin:2px 0 0;font-size:12px;color:#6c5ce7;">{{ product.price }}EUR</p>\n'
            '                </a>\n'
            '              </td>\n'
            '              {% endfor %}\n'
            '            </tr>\n'
            '          </table>\n'
            '        </td></tr>\n'
            '        <!-- Footer -->\n'
            '        <tr><td style="padding:20px 40px;background-color:#f4f4f7;text-align:center;border-top:1px solid #eee;">\n'
            '          <p style="margin:0 0 8px;font-size:12px;color:#999;">Cette offre est personnelle et non cumulable.</p>\n'
            '          <a href="{{ subscription_management_url }}" style="font-size:12px;color:#999;text-decoration:underline;">Se desabonner</a>\n'
            '        </td></tr>\n'
            '      </table>\n'
            '    </td></tr>\n'
            '  </table>\n'
            '</body>\n'
            '</html>'
        ),
    },

    # =========================================================================
    # PUSH NOTIFICATION TEMPLATE
    # =========================================================================
    "push_notification": {
        "name": "Push Notification",
        "description": "Notification push mobile avec titre, corps, image et deep link",
        "icon": "push",
        "category": "push",
        "structure": {
            "required": ["title", "body", "deep_link"],
            "optional": [
                "image_url",
                "action_button_1_text",
                "action_button_1_url",
                "action_button_2_text",
                "action_button_2_url",
            ],
        },
        "example_brief": (
            "Push notification promo flash pour app e-commerce, "
            "personnalise avec prenom et ville, derniere categorie consultee, "
            "deep link vers /promo, 2 boutons d'action (Voir / Plus tard)"
        ),
        "html_skeleton": (
            '{\n'
            '  "title": "{{ ${first_name} | default: \'Hey\' }} ! Offre speciale a {{ ${city} | default: \'proximite\' }}",\n'
            '  "body": "Decouvrez nos promos {{ custom_attribute.${last_viewed_category} | default: \'exclusives\' }}. -30% aujourd\'hui seulement !",\n'
            '  "image_url": "https://cdn.example.com/push/promo-banner.jpg",\n'
            '  "deep_link": "app://promo/flash-sale",\n'
            '  "action_buttons": [\n'
            '    { "text": "Voir les offres", "url": "app://promo/flash-sale" },\n'
            '    { "text": "Plus tard", "url": "app://dismiss" }\n'
            '  ]\n'
            '}'
        ),
    },

    # =========================================================================
    # SMS TEMPLATE
    # =========================================================================
    "sms_message": {
        "name": "SMS",
        "description": "Message SMS court avec lien et opt-out (max 160 chars)",
        "icon": "sms",
        "category": "sms",
        "structure": {
            "required": ["message_text", "short_link"],
            "optional": [
                "promo_code",
                "opt_out_text",
            ],
        },
        "example_brief": (
            "SMS promo pour soldes d'ete, personnalise avec prenom, "
            "code promo ETE25, lien court vers le site, mention STOP pour opt-out"
        ),
        "html_skeleton": (
            '{{ ${first_name} | default: \'Cher client\' }}, '
            'profitez de -25% avec le code {{ event_properties.${promo_code} | default: \'ETE25\' }} ! '
            'Offre valable 48h : {{ ${short_url} | default: \'https://bit.ly/promo\' }} '
            'STOP au 36200'
        ),
    },
}


def get_templates(category: str | None = None) -> list[dict[str, Any]]:
    """Retourne la liste des templates disponibles.

    Args:
        category: Filtre optionnel par categorie ('banner', 'email', 'push', 'sms').
                  Si None, retourne tous les templates.
    """
    result = []
    for key, value in TEMPLATES.items():
        if category is not None and value.get("category") != category:
            continue
        result.append({"key": key, "id": key, **value})
    return result


def get_template(name: str) -> dict[str, Any] | None:
    """Retourne un template par son identifiant (ex: 'hero_banner').

    Retourne None si le template n'existe pas.
    """
    tpl = TEMPLATES.get(name)
    if tpl is None:
        return None
    return {"key": name, "id": name, **tpl}
