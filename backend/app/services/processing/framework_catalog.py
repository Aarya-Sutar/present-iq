from dataclasses import dataclass


@dataclass(frozen=True)
class FrameworkDefinition:
    name: str
    description: str
    keywords: tuple[str, ...]
    references: tuple[str, ...]


FRAMEWORKS: tuple[FrameworkDefinition, ...] = (
    FrameworkDefinition(
        name="SWOT Analysis",
        description="Internal strengths and weaknesses against external opportunities and threats.",
        keywords=("swot", "strengths", "weaknesses", "opportunities", "threats"),
        references=(
            "A SWOT slide compares internal strengths and weaknesses with external opportunities and threats.",
            "Use this framework when the deck summarizes strategic position, risk, and advantage.",
        ),
    ),
    FrameworkDefinition(
        name="Business Model Canvas",
        description="A structured view of value proposition, customers, channels, revenue, and costs.",
        keywords=(
            "business model canvas",
            "value proposition",
            "customer segments",
            "revenue streams",
            "channels",
            "cost structure",
            "key partners",
            "key activities",
            "key resources",
        ),
        references=(
            "A BMC slide often maps value proposition, customer segments, channels, revenue streams, and cost structure.",
            "This framework is used to explain how the business creates, delivers, and captures value.",
        ),
    ),
    FrameworkDefinition(
        name="4Ps Marketing",
        description="Product, price, place, and promotion marketing mix.",
        keywords=("4ps", "marketing mix", "product", "price", "place", "promotion"),
        references=(
            "A 4Ps slide discusses product, price, place, and promotion.",
            "Use this framework for go-to-market and marketing mix planning.",
        ),
    ),
    FrameworkDefinition(
        name="STP Framework",
        description="Segmentation, targeting, and positioning.",
        keywords=("stp", "segmentation", "targeting", "positioning", "customer segment"),
        references=(
            "An STP slide explains how the market is segmented, which segment is targeted, and how the product is positioned.",
            "Use this when the deck narrows the market and defines a clear target customer.",
        ),
    ),
    FrameworkDefinition(
        name="Porter's Five Forces",
        description="Industry attractiveness through competitive forces.",
        keywords=(
            "five forces",
            "rivalry",
            "new entrants",
            "suppliers",
            "buyers",
            "substitutes",
            "competitive forces",
        ),
        references=(
            "A Five Forces slide assesses rivalry, threat of new entrants, supplier power, buyer power, and substitutes.",
            "This framework is used to evaluate industry structure and competitive intensity.",
        ),
    ),
    FrameworkDefinition(
        name="PESTEL Analysis",
        description="Political, economic, social, technological, environmental, and legal factors.",
        keywords=("pestel", "political", "economic", "social", "technological", "environmental", "legal"),
        references=(
            "A PESTEL slide reviews political, economic, social, technological, environmental, and legal factors.",
            "Use this framework when the slide discusses macro-environmental drivers.",
        ),
    ),
    FrameworkDefinition(
        name="Value Chain Analysis",
        description="Primary and support activities that create value.",
        keywords=("value chain", "inbound logistics", "operations", "outbound logistics", "marketing", "service"),
        references=(
            "A value chain slide breaks the business into primary and support activities.",
            "This framework shows where value is created and where efficiency can improve.",
        ),
    ),
    FrameworkDefinition(
        name="KPI Dashboard",
        description="Operational metrics and performance indicators.",
        keywords=("kpi", "dashboard", "metrics", "okr", "performance", "targets", "tracking"),
        references=(
            "A KPI dashboard slide shows metrics, targets, and performance trends.",
            "Use this when the deck is tracking execution and measurable outcomes.",
        ),
    ),
    FrameworkDefinition(
        name="Market Segmentation",
        description="Segmenting the market into distinct customer groups.",
        keywords=("market segmentation", "segment", "cohort", "persona", "user group", "customer group"),
        references=(
            "A market segmentation slide breaks the market into customer groups with different needs.",
            "This framework is used to show the structure of the addressable market.",
        ),
    ),
    FrameworkDefinition(
        name="Customer Journey Mapping",
        description="Stages, touchpoints, and user experience flow.",
        keywords=("customer journey", "touchpoint", "journey", "onboarding", "retention", "experience flow"),
        references=(
            "A customer journey slide maps stages, touchpoints, and friction points in the user experience.",
            "Use this framework when the deck describes how a user moves from awareness to retention.",
        ),
    ),
    FrameworkDefinition(
        name="Competitor Analysis",
        description="Direct and indirect competitor comparison and differentiation.",
        keywords=("competitor", "competition", "benchmark", "differentiation", "competitive advantage", "vs"),
        references=(
            "A competitor analysis slide compares the startup against LinkedIn, Discord, WhatsApp, Instagram, or other alternatives.",
            "This framework discusses advantages, disadvantages, differentiation, strengths, weaknesses, or comparison with competitors.",
            "Use this framework when the deck compares features, positioning, or competitive advantage.",
        ),
    ),
    FrameworkDefinition(
        name="Financial Model",
        description="Revenue, cost, burn, runway, projections, and unit economics.",
        keywords=("revenue", "cost", "burn", "runway", "projection", "funding", "unit economics", "cash flow"),
        references=(
            "A financial model slide discusses revenue, subscriptions, pricing, monetization, burn, runway, projections, or funding.",
            "Use this framework when the presentation explains how the startup earns money or manages financial growth.",
            "Monetization plans, pricing models, subscription plans, and revenue streams belong to financial modeling.",
        ),
    ),
    FrameworkDefinition(
        name="Go-To-Market Strategy",
        description="Launch, acquisition, channels, and adoption plan.",
        keywords=("go-to-market", "gtm", "launch", "acquisition", "channel", "adoption", "distribution"),
        references=(
            "A go-to-market slide explains launch strategy, marketing channels, adoption, influencer marketing, distribution, or promotions.",
            "This framework includes WhatsApp marketing, creator promotion, student ambassadors, Instagram ads, and launch campaigns.",
            "Use this framework when the startup explains how users will be acquired and growth will happen.",
        ),
    ),
)