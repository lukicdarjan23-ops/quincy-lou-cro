import * as cheerio from "cheerio";
import type { Element } from "domhandler";
import type { FetchedPage } from "@/lib/fetch-page";
import { MIN_WORD_COUNT } from "@/lib/config";

/* ------------------------------------------------------------------ types */

export type CtaElement = {
  text: string;
  kind: "button" | "link" | "input" | "role_button";
  href: string | null;
  buttonStyled: boolean;
  classification: "generic" | "value_specific";
  classificationSignal: string;
  location: "header_or_hero" | "body";
};

export type TestimonialBlock = {
  excerpt: string;
  wordCount: number;
  hasName: boolean;
  hasTitleOrCompany: boolean;
  hasPhoto: boolean;
  photoLooksLikeStock: boolean | null;
  hasSpecificDetail: boolean;
  readsAsGenericPraise: boolean;
};

export type LinkRecord = {
  text: string;
  href: string;
  area: "nav" | "footer" | "body";
  destination: "internal" | "external";
};

export type FormField = {
  label: string;
  name: string;
  type: string;
  required: boolean;
};

export type FactSheet = {
  url: string;
  finalUrl: string;
  fetchTruncated: boolean;
  lang: string | null;
  title: string | null;
  metaDescription: string | null;
  wordCount: number;
  insufficientContent: boolean;
  h1s: string[];
  headingStructure: { tag: string; text: string }[];
  firstScreen: { textSample: string; headings: string[] };
  ctas: CtaElement[];
  ctaSummary: {
    total: number;
    generic: number;
    valueSpecific: number;
    buttonStyled: number;
    distinctPrimaryCtas: number;
    repeatedPrimaryCtaTexts: string[];
    inHeaderOrHero: number;
    noneFound: boolean;
  };
  phone: { found: boolean; inHeaderOrHero: boolean; telLinks: number; samples: string[] };
  testimonials: { count: number; blocks: TestimonialBlock[] };
  imageryNearTestimonials: {
    imagesFound: number;
    likelyStockCount: number;
    signals: string[];
    note: string;
  };
  socialProofNumbers: string[];
  trustBadges: { mentions: { text: string; nearCta: boolean }[]; anyNearCta: boolean };
  forms: {
    count: number;
    totalFields: number;
    requiredFields: number;
    fields: FormField[];
  };
  links: {
    totalAnchors: number;
    contactOrInPageLinks: number;
    internal: number;
    external: number;
    navLinks: LinkRecord[];
    outboundNonCta: LinkRecord[];
    exitCount: number;
  };
  urgency: {
    anyFound: boolean;
    phrases: { phrase: string; sentence: string; backedBySpecific: boolean }[];
  };
  images: { total: number; withAlt: number };
  visibleText: string;
};

/* -------------------------------------------------------------- constants */

const GENERIC_CTA_PHRASES = new Set([
  "submit",
  "send",
  "send message",
  "click here",
  "click",
  "click now",
  "learn more",
  "read more",
  "more",
  "more info",
  "more information",
  "find out more",
  "see more",
  "view more",
  "view details",
  "details",
  "continue",
  "next",
  "go",
  "here",
  "start",
  "get started",
  "sign up",
  "subscribe",
  "enter",
  "apply",
  "explore",
  "discover",
  "contact",
  "contact us",
  "our services",
  "services",
  "about us",
  "ok",
]);

const VALUE_WORDS = [
  "free",
  "my ",
  "your ",
  "quote",
  "estimate",
  "demo",
  "trial",
  "consultation",
  "audit",
  "book",
  "schedule",
  "appointment",
  "call now",
  "price",
  "pricing",
  "save",
  "guide",
  "checklist",
  "report",
  "today",
  "same day",
  "no obligation",
  "instant",
];

const ACTION_WORDS = [
  "get",
  "book",
  "call",
  "schedule",
  "request",
  "start",
  "buy",
  "order",
  "claim",
  "download",
  "join",
  "try",
  "quote",
  "estimate",
  "contact",
  "apply",
  "sign",
  "subscribe",
  "shop",
  "reserve",
  "talk",
  "speak",
  "send",
  "submit",
  "learn",
  "see",
  "view",
  "find",
];

/**
 * Rough stand-in for "the first visible screen": everything inside a header
 * or hero container, plus every element up to this much body text.
 */
const FIRST_SCREEN_TEXT_BUDGET = 700;

const BUTTON_CLASS_PATTERN = /(^|[\s_-])(btn|button|cta)([\s_-]|$)|btn-|-btn|button-|-button|\bcta-|-cta\b/i;

const CTA_HREF_PATTERN =
  /(^|[/?#&=_-])(contact|quote|estimate|book|booking|schedule|signup|sign-up|register|apply|checkout|cart|demo|trial|call|get-started|free)([/?#&=_.-]|$)/i;

const TESTIMONIAL_CLASS_PATTERN = /(testimonial|review|quote|feedback|rating|customer-say|what-.*-say)/i;

const STOCK_IMAGE_SIGNALS = [
  "shutterstock",
  "istockphoto",
  "istock",
  "gettyimages",
  "getty",
  "unsplash",
  "pexels",
  "pixabay",
  "adobestock",
  "stock-photo",
  "stock_photo",
  "stockphoto",
  "depositphotos",
  "freepik",
  "placeholder",
  "placehold",
  "avatar",
  "default-user",
  "default_user",
  "dummy",
  "sample-",
  "person-1",
  "person1",
  "user-1",
  "headshot-",
  "smiling-",
  "businessman",
  "businesswoman",
];

const TRUST_BADGE_PATTERNS: { label: string; pattern: RegExp }[] = [
  { label: "money-back guarantee", pattern: /money[-\s]?back|satisfaction guarantee(d)?/i },
  { label: "guarantee", pattern: /\bguarantee(d|s)?\b/i },
  { label: "warranty", pattern: /\bwarrant(y|ies)\b/i },
  { label: "licensed / insured / bonded", pattern: /\blicen[cs]ed\b|\binsured\b|\bbonded\b/i },
  { label: "BBB / accreditation", pattern: /better business bureau|\bbbb\b|accredited/i },
  { label: "certification", pattern: /\bcertified\b|\bcertification\b|\bISO \d/i },
  { label: "secure / SSL", pattern: /\bssl\b|secure checkout|256-bit|encrypted/i },
  { label: "third-party review platform", pattern: /trustpilot|google reviews|yelp|angi\b|houzz/i },
  { label: "no-obligation promise", pattern: /no obligation|no pressure|cancel anytime/i },
  { label: "award", pattern: /\baward[- ]winning\b|\bwinner of\b|\bvoted best\b/i },
];

const URGENCY_PATTERNS: RegExp[] = [
  /limited time/i,
  /limited (slots|spots|spaces|availability|offer)/i,
  /today only/i,
  /act now/i,
  /hurry/i,
  /last chance/i,
  /ends (soon|today|tonight|tomorrow)/i,
  /only \d+ (left|remaining|spots|slots|seats)/i,
  /spots? (left|remaining)/i,
  /while supplies last/i,
  /offer expires/i,
  /countdown/i,
  /book (now|today) before/i,
  /don'?t miss/i,
  /deadline/i,
];

const SOCIAL_PROOF_PATTERNS: RegExp[] = [
  /\b\d[\d,]*\+?\s*(clients?|customers?|patients?|members?|families|businesses|companies|homes?|projects?|jobs?|installations?|reviews?|ratings?|users?|students?)\b/gi,
  /\b(over|more than|serving)\s+\d[\d,]*\+?\b/gi,
  /\bsince\s+(19|20)\d{2}\b/gi,
  /\b\d{1,3}\+?\s*years?\s+(of\s+)?(experience|in business|serving)\b/gi,
  /\b\d(\.\d)?\s*(\/\s*5|out of 5|star(s)?)\b/gi,
  /\b\d{1,3}(\.\d)?%\s*(of|satisfaction|success|approval)?/gi,
];

/* ---------------------------------------------------------------- helpers */

function squash(value: string | null | undefined): string {
  return (value ?? "").replace(/\s+/g, " ").trim();
}

function cap(value: string, max: number): string {
  return value.length <= max ? value : `${value.slice(0, max).trimEnd()}...`;
}

function countWords(value: string): number {
  const matched = value.match(/[A-Za-zÀ-ÿ0-9'’-]+/g);
  return matched ? matched.length : 0;
}

function unique(values: string[]): string[] {
  return [...new Set(values.map((value) => value.trim()).filter(Boolean))];
}

function classifyCtaText(text: string): {
  classification: "generic" | "value_specific";
  signal: string;
} {
  const normalized = squash(text).toLowerCase().replace(/[^a-z0-9 ]/g, " ").replace(/\s+/g, " ").trim();

  if (!normalized) {
    return { classification: "generic", signal: "no readable label (icon or empty element)" };
  }
  if (GENERIC_CTA_PHRASES.has(normalized)) {
    return { classification: "generic", signal: `exact generic label "${normalized}"` };
  }

  const padded = ` ${normalized} `;
  const hits = VALUE_WORDS.filter((word) => padded.includes(word.trim() === word ? ` ${word} ` : word));
  if (hits.length > 0) {
    return {
      classification: "value_specific",
      signal: `names what the visitor gets (${hits.map((h) => h.trim()).join(", ")})`,
    };
  }

  const words = normalized.split(" ");
  if (words.length <= 3) {
    return {
      classification: "generic",
      signal: `short action-only label with no stated outcome ("${normalized}")`,
    };
  }

  return {
    classification: "generic",
    signal: `describes an action, not an outcome ("${cap(normalized, 60)}")`,
  };
}

function looksLikeStockImage(src: string, alt: string, className: string): boolean {
  const haystack = `${src} ${alt} ${className}`.toLowerCase();
  return STOCK_IMAGE_SIGNALS.some((signal) => haystack.includes(signal));
}

function digitCount(value: string): number {
  return (value.match(/\d/g) ?? []).length;
}

function splitSentences(text: string): string[] {
  return text
    .split(/(?<=[.!?])\s+|\n+/)
    .map((sentence) => squash(sentence))
    .filter(Boolean);
}

/* ------------------------------------------------------------ fact sheet */

export function buildFactSheet(page: FetchedPage): FactSheet {
  const $ = cheerio.load(page.html);

  // Second pass used only for readable text, with boilerplate stripped.
  const $text = cheerio.load(page.html);
  $text("script, style, noscript, template, svg, iframe, nav, footer, [role='navigation'], [aria-hidden='true']").remove();
  const visibleText = squash($text("body").text());
  const wordCount = countWords(visibleText);

  const baseUrl = page.finalUrl;
  let baseHost = "";
  try {
    baseHost = new URL(baseUrl).hostname.toLowerCase();
  } catch {
    baseHost = "";
  }

  /* ---- element ordering, used to approximate "first visible screen" ---- */

  const bodyElements = $("body *").toArray() as Element[];
  const indexOf = new Map<Element, number>();
  bodyElements.forEach((element, index) => indexOf.set(element, index));

  const heroRoots: Element[] = [];
  let runningTextLength = 0;
  let firstScreenCutoff = bodyElements.length;

  bodyElements.forEach((element, index) => {
    const tag = element.tagName?.toLowerCase() ?? "";
    const attrs = `${element.attribs?.class ?? ""} ${element.attribs?.id ?? ""} ${element.attribs?.role ?? ""}`.toLowerCase();
    if (tag === "header" || /hero|banner|masthead|jumbotron|above-fold/.test(attrs)) {
      heroRoots.push(element);
    }
    if (!["script", "style", "noscript", "template"].includes(tag)) {
      for (const child of element.children ?? []) {
        if (child.type === "text") {
          runningTextLength += squash((child as unknown as { data: string }).data).length;
        }
      }
    }
    if (runningTextLength > FIRST_SCREEN_TEXT_BUDGET && firstScreenCutoff === bodyElements.length) {
      firstScreenCutoff = index;
    }
  });

  const heroSet = new Set<Element>();
  for (const root of heroRoots) {
    heroSet.add(root);
    for (const descendant of $(root).find("*").toArray() as Element[]) {
      heroSet.add(descendant);
    }
  }

  const isFirstScreen = (element: Element): boolean => {
    if (heroSet.has(element)) return true;
    const index = indexOf.get(element);
    return index !== undefined && index <= firstScreenCutoff;
  };

  const firstScreenElements = bodyElements.filter(isFirstScreen);
  const firstScreenText = squash(
    firstScreenElements
      .map((element) =>
        (element.children ?? [])
          .filter((child) => child.type === "text")
          .map((child) => (child as unknown as { data: string }).data)
          .join(" "),
      )
      .join(" "),
  );

  /* ------------------------------------------------------- headings ---- */

  const headingStructure = ($("h1, h2, h3, h4, h5, h6").toArray() as Element[])
    .map((element) => ({
      tag: element.tagName.toLowerCase(),
      text: cap(squash($(element).text()), 160),
    }))
    .filter((heading) => heading.text.length > 0)
    .slice(0, 60);

  const h1s = ($("h1").toArray() as Element[])
    .map((element) => cap(squash($(element).text()), 200))
    .filter(Boolean);

  const firstScreenHeadings = ($("h1, h2, h3").toArray() as Element[])
    .filter(isFirstScreen)
    .map((element) => cap(squash($(element).text()), 160))
    .filter(Boolean)
    .slice(0, 10);

  /* ----------------------------------------------------------- CTAs ---- */

  const ctaNodes = new Set<Element>();
  const ctas: CtaElement[] = [];

  const candidates = $("a, button, input[type='submit'], input[type='button'], [role='button']").toArray() as Element[];

  for (const element of candidates) {
    const $element = $(element);
    const tag = element.tagName?.toLowerCase() ?? "";
    const className = element.attribs?.class ?? "";
    const role = (element.attribs?.role ?? "").toLowerCase();
    const rawText =
      tag === "input"
        ? element.attribs?.value ?? ""
        : squash($element.text()) || squash($element.attr("aria-label")) || squash($element.attr("title"));
    const text = squash(rawText);
    const href = tag === "a" ? $element.attr("href") ?? null : null;
    const buttonStyled =
      tag === "button" ||
      tag === "input" ||
      role === "button" ||
      BUTTON_CLASS_PATTERN.test(className);

    const actionable =
      tag === "button" ||
      tag === "input" ||
      role === "button" ||
      buttonStyled ||
      (href ? /^(tel:|mailto:)/i.test(href) || CTA_HREF_PATTERN.test(href.replace(/^https?:\/\/[^/]+/i, "")) : false) ||
      ACTION_WORDS.some((word) => new RegExp(`^${word}\\b`, "i").test(text));

    if (!actionable) continue;
    if (!text && !href) continue;

    const isPhoneLink = href ? /^tel:/i.test(href) : false;
    const { classification, signal } = isPhoneLink
      ? {
          classification: "value_specific" as const,
          signal: "click-to-call phone number, the visitor knows exactly what happens",
        }
      : classifyCtaText(text);
    ctaNodes.add(element);
    ctas.push({
      text: cap(text || "(no label)", 120),
      kind:
        tag === "button" ? "button" : tag === "input" ? "input" : role === "button" ? "role_button" : "link",
      href: href ? cap(href, 200) : null,
      buttonStyled,
      classification,
      classificationSignal: signal,
      location: isFirstScreen(element) ? "header_or_hero" : "body",
    });
  }

  const buttonStyledCtas = ctas.filter((cta) => cta.buttonStyled);
  const primaryCtaCounts = new Map<string, number>();
  for (const cta of buttonStyledCtas) {
    const key = cta.text.toLowerCase();
    primaryCtaCounts.set(key, (primaryCtaCounts.get(key) ?? 0) + 1);
  }

  const ctaSummary = {
    total: ctas.length,
    generic: ctas.filter((cta) => cta.classification === "generic").length,
    valueSpecific: ctas.filter((cta) => cta.classification === "value_specific").length,
    buttonStyled: buttonStyledCtas.length,
    distinctPrimaryCtas: primaryCtaCounts.size,
    repeatedPrimaryCtaTexts: [...primaryCtaCounts.entries()]
      .filter(([, count]) => count > 1)
      .map(([text, count]) => `${text} (x${count})`)
      .slice(0, 10),
    inHeaderOrHero: ctas.filter((cta) => cta.location === "header_or_hero").length,
    noneFound: ctas.length === 0,
  };

  /* ---------------------------------------------------------- phone ---- */

  const telLinks = ($("a[href^='tel:']").toArray() as Element[]);
  const phoneCandidates = unique(
    (visibleText.match(/\+?\(?\d[\d\s().\-]{7,}\d/g) ?? [])
      .map((match) => squash(match))
      .filter((match) => {
        const digits = digitCount(match);
        return digits >= 9 && digits <= 15;
      }),
  ).slice(0, 5);

  const telInFirstScreen = telLinks.some(isFirstScreen);
  const phoneInFirstScreenText = phoneCandidates.some((candidate) => firstScreenText.includes(candidate));

  const phone = {
    found: phoneCandidates.length > 0 || telLinks.length > 0,
    inHeaderOrHero: telInFirstScreen || phoneInFirstScreenText,
    telLinks: telLinks.length,
    samples: phoneCandidates,
  };

  /* --------------------------------------------------- testimonials ---- */

  const testimonialCandidates = ($("blockquote, [class], [id]").toArray() as Element[]).filter((element) => {
    const tag = element.tagName?.toLowerCase() ?? "";
    if (tag === "blockquote") return true;
    const attrs = `${element.attribs?.class ?? ""} ${element.attribs?.id ?? ""}`;
    return TESTIMONIAL_CLASS_PATTERN.test(attrs);
  });

  const candidateSet = new Set(testimonialCandidates);
  const topLevelTestimonials = testimonialCandidates.filter((element) => {
    const ancestors = $(element).parents().toArray() as Element[];
    return !ancestors.some((ancestor) => candidateSet.has(ancestor));
  });

  let testimonialImages = 0;
  let likelyStockImages = 0;
  const stockSignals: string[] = [];

  const testimonialBlocks: TestimonialBlock[] = topLevelTestimonials.slice(0, 10).map((element) => {
    const $element = $(element);
    const text = squash($element.text());
    const words = countWords(text);
    const images = $element.find("img").toArray() as Element[];
    testimonialImages += images.length;

    let photoLooksLikeStock: boolean | null = images.length > 0 ? false : null;
    for (const image of images) {
      const src = image.attribs?.src ?? image.attribs?.["data-src"] ?? "";
      const alt = image.attribs?.alt ?? "";
      const className = image.attribs?.class ?? "";
      if (looksLikeStockImage(src, alt, className)) {
        photoLooksLikeStock = true;
        likelyStockImages += 1;
        stockSignals.push(cap(squash(`${src} ${alt}`), 120));
      }
    }

    const attribution = squash(
      $element.find("cite, footer, figcaption, [class*='author'], [class*='name'], [class*='customer']").text(),
    );
    const hasName =
      attribution.length > 0 ||
      /[-–—]\s*[A-Z][a-z]+(\s+[A-Z][a-z.]+)?\s*$/.test(text) ||
      /\b[A-Z][a-z]+\s+[A-Z]\.\s*$/.test(text);

    const hasTitleOrCompany =
      /\b(ceo|owner|founder|president|director|manager|principal|partner|dr\.?|md|dds|homeowner|verified (buyer|customer))\b/i.test(
        `${text} ${attribution}`,
      ) || /,\s*[A-Z][A-Za-z&. ]{2,30}(inc|llc|ltd|co\.|company|corp)\b/i.test(`${text} ${attribution}`);

    const hasSpecificDetail = /\d/.test(text) || words >= 25;

    return {
      excerpt: cap(text, 400),
      wordCount: words,
      hasName,
      hasTitleOrCompany,
      hasPhoto: images.length > 0,
      photoLooksLikeStock,
      hasSpecificDetail,
      readsAsGenericPraise: words > 0 && words < 12 && !/\d/.test(text),
    };
  });

  /* ------------------------------------------------ social proof nums -- */

  const socialProofNumbers: string[] = [];
  for (const pattern of SOCIAL_PROOF_PATTERNS) {
    const matches = visibleText.match(pattern);
    if (matches) {
      socialProofNumbers.push(...matches.map((match) => squash(match)));
    }
  }

  /* ---------------------------------------------------- trust badges --- */

  const nearCta = (element: Element): boolean => {
    let current: Element | undefined = element;
    for (let level = 0; level < 3 && current; level += 1) {
      const parent: Element | undefined = $(current).parent().get(0) as Element | undefined;
      if (!parent) break;
      const inside = $(parent).find("a, button, input[type='submit'], [role='button']").toArray() as Element[];
      if (inside.some((node) => ctaNodes.has(node))) return true;
      current = parent;
    }
    return false;
  };

  const badgeMentions: { text: string; nearCta: boolean }[] = [];
  const seenBadges = new Set<string>();

  for (const { label, pattern } of TRUST_BADGE_PATTERNS) {
    if (!pattern.test(visibleText)) continue;

    const holder = (bodyElements.find((element) => {
      const ownText = squash(
        (element.children ?? [])
          .filter((child) => child.type === "text")
          .map((child) => (child as unknown as { data: string }).data)
          .join(" "),
      );
      return ownText.length > 0 && pattern.test(ownText);
    }) ?? null) as Element | null;

    const sentence =
      splitSentences(visibleText).find((candidate) => pattern.test(candidate)) ?? label;
    const key = sentence.slice(0, 60).toLowerCase();
    if (seenBadges.has(key)) continue;
    seenBadges.add(key);

    badgeMentions.push({
      text: `${label}: "${cap(sentence, 160)}"`,
      nearCta: holder ? nearCta(holder) : false,
    });
  }

  /* ---------------------------------------------------------- forms ---- */

  const formElements = $("form").toArray() as Element[];
  const formFields: FormField[] = [];
  let requiredFields = 0;

  for (const form of formElements) {
    const fields = $(form)
      .find("input, select, textarea")
      .toArray() as Element[];
    for (const field of fields) {
      const type = (field.attribs?.type ?? (field.tagName === "select" ? "select" : field.tagName === "textarea" ? "textarea" : "text")).toLowerCase();
      if (["hidden", "submit", "button", "image", "reset"].includes(type)) continue;

      const name = field.attribs?.name ?? field.attribs?.id ?? "";
      const id = field.attribs?.id;
      const labelText =
        (id ? squash($(`label[for='${id}']`).first().text()) : "") ||
        squash($(field).closest("label").text()) ||
        squash(field.attribs?.placeholder ?? "") ||
        squash(field.attribs?.["aria-label"] ?? "");
      const required = field.attribs?.required !== undefined || field.attribs?.["aria-required"] === "true";
      if (required) requiredFields += 1;

      formFields.push({
        label: cap(labelText || name || type, 80),
        name: cap(name, 60),
        type,
        required,
      });
    }
  }

  /* ---------------------------------------------------------- links ---- */

  const anchors = ($("a[href]").toArray() as Element[]);
  const navLinks: LinkRecord[] = [];
  const outboundNonCta: LinkRecord[] = [];
  let internalCount = 0;
  let externalCount = 0;
  let contactOrInPageLinks = 0;
  const exitHrefs = new Set<string>();

  for (const anchor of anchors) {
    const hrefRaw = anchor.attribs?.href ?? "";
    if (!hrefRaw) continue;
    if (hrefRaw.startsWith("#") || /^(javascript:|mailto:|tel:)/i.test(hrefRaw)) {
      contactOrInPageLinks += 1;
      continue;
    }

    let resolved: URL | null = null;
    try {
      resolved = new URL(hrefRaw, baseUrl);
    } catch {
      resolved = null;
    }
    if (!resolved) continue;

    const destination: "internal" | "external" =
      resolved.hostname.toLowerCase() === baseHost ? "internal" : "external";
    if (destination === "internal") internalCount += 1;
    else externalCount += 1;

    const ancestors = ($(anchor).parents().toArray() as Element[]).map((element) =>
      (element.tagName ?? "").toLowerCase(),
    );
    const area: "nav" | "footer" | "body" = ancestors.includes("nav")
      ? "nav"
      : ancestors.includes("footer")
        ? "footer"
        : ancestors.includes("header")
          ? "nav"
          : "body";

    const record: LinkRecord = {
      text: cap(squash($(anchor).text()) || "(no label)", 80),
      href: cap(resolved.toString(), 180),
      area,
      destination,
    };

    if (area === "nav" || area === "footer") {
      navLinks.push(record);
    }

    const isCta = ctaNodes.has(anchor);
    if (!isCta) {
      exitHrefs.add(resolved.toString());
      if (area === "body") outboundNonCta.push(record);
    }
  }

  /* --------------------------------------------------------- urgency --- */

  const sentences = splitSentences(visibleText);
  const urgencyPhrases: { phrase: string; sentence: string; backedBySpecific: boolean }[] = [];

  for (const pattern of URGENCY_PATTERNS) {
    const sentence = sentences.find((candidate) => pattern.test(candidate));
    if (!sentence) continue;
    const match = sentence.match(pattern);
    const backedBySpecific =
      /\d/.test(sentence) ||
      /\b(january|february|march|april|may|june|july|august|september|october|november|december|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b/i.test(
        sentence,
      ) ||
      /\buntil\b|\bby\s+\w+day\b/i.test(sentence);

    urgencyPhrases.push({
      phrase: squash(match?.[0] ?? ""),
      sentence: cap(sentence, 200),
      backedBySpecific,
    });
    if (urgencyPhrases.length >= 10) break;
  }

  /* ---------------------------------------------------------- images --- */

  const imageElements = ($("img").toArray() as Element[]);
  const imagesWithAlt = imageElements.filter((image) => squash(image.attribs?.alt ?? "").length > 0).length;

  /* ----------------------------------------------------------- done ---- */

  return {
    url: page.requestedUrl,
    finalUrl: page.finalUrl,
    fetchTruncated: page.truncated,
    lang: squash($("html").attr("lang") ?? "") || null,
    title: squash($("title").first().text()) || null,
    metaDescription: squash($("meta[name='description']").attr("content") ?? "") || null,
    wordCount,
    insufficientContent: wordCount < MIN_WORD_COUNT,
    h1s,
    headingStructure,
    firstScreen: {
      textSample: cap(firstScreenText, 1200),
      headings: firstScreenHeadings,
    },
    ctas: ctas.slice(0, 30),
    ctaSummary,
    phone,
    testimonials: { count: topLevelTestimonials.length, blocks: testimonialBlocks },
    imageryNearTestimonials: {
      imagesFound: testimonialImages,
      likelyStockCount: likelyStockImages,
      signals: unique(stockSignals).slice(0, 8),
      note: "Inferred from file names, alt text and CSS classes only. No image was rendered or inspected visually.",
    },
    socialProofNumbers: unique(socialProofNumbers).slice(0, 15),
    trustBadges: {
      mentions: badgeMentions.slice(0, 12),
      anyNearCta: badgeMentions.some((mention) => mention.nearCta),
    },
    forms: {
      count: formElements.length,
      totalFields: formFields.length,
      requiredFields,
      fields: formFields.slice(0, 25),
    },
    links: {
      totalAnchors: internalCount + externalCount,
      contactOrInPageLinks,
      internal: internalCount,
      external: externalCount,
      navLinks: navLinks.slice(0, 30),
      outboundNonCta: outboundNonCta.slice(0, 30),
      exitCount: exitHrefs.size,
    },
    urgency: { anyFound: urgencyPhrases.length > 0, phrases: urgencyPhrases },
    images: { total: imageElements.length, withAlt: imagesWithAlt },
    visibleText,
  };
}

/** The fact sheet minus the full page text, which is sent separately. */
export function factSheetForPrompt(factSheet: FactSheet): Omit<FactSheet, "visibleText"> {
  const { visibleText: _visibleText, ...rest } = factSheet;
  return rest;
}

export function trimmedPageText(factSheet: FactSheet, maxChars = 12_000): string {
  return cap(factSheet.visibleText, maxChars);
}
