import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.database import connect_to_mongo, close_mongo_connection
import app.database as db
from app.embedding_service import build_company_context, generate_embedding

SEED_COMPANIES: List[Dict[str, Any]] = [
    # 1. User's specific example
    {
        "company_name": "Apex Financial UAE",
        "country": "UAE",
        "state_region": "Dubai",
        "city": "Dubai",
        "primary_industry": "finance",
        "business_type": "agency",
        "min_order_qty": 50,
        "company_size": "10-50 employees",
        "funding_stage": "seeding",
        "is_verified_business": True,
        "company_bio": "B2B financial agency providing micro-lending, factoring, and customized working capital debt structures for startups.",
        "core_team_designations": "Managing Partner, Lead Accountant, Risk Officer",
        "specialties": "microfinance, startup loans, debt structuring, financial advisory",
        "product_service_offerings": "working capital loans, structured credit advisory"
    },
    # 2. UAE FinTech Series A verified (original sample)
    {
        "company_name": "Apex PayTech",
        "country": "UAE",
        "state_region": "Dubai",
        "city": "Dubai",
        "primary_industry": "FinTech",
        "business_type": "SaaS Provider",
        "min_order_qty": 1,
        "company_size": "50-200 employees",
        "funding_stage": "Series A",
        "is_verified_business": True,
        "company_bio": "We provide scalable digital payment infrastructure, online payment gateways, and merchant services.",
        "core_team_designations": "CEO, CTO, Head of Payments",
        "specialties": "payment gateway, API payments, card processing",
        "product_service_offerings": "online payment gateway, recurring billing, payout automation"
    },
    # 3. UAE FinTech Series A verified
    {
        "company_name": "HalalVest",
        "country": "UAE",
        "state_region": "Abu Dhabi",
        "city": "Abu Dhabi",
        "primary_industry": "FinTech",
        "business_type": "SaaS Provider",
        "min_order_qty": 1,
        "company_size": "10-50 employees",
        "funding_stage": "Series A",
        "is_verified_business": True,
        "company_bio": "Sharia-compliant digital investment platform offering micro-investments and automated wealth management.",
        "core_team_designations": "CEO, Shariah Advisor, Lead Engineer",
        "specialties": "halal investing, ethical finance, wealthtech",
        "product_service_offerings": "micro-investment API, robo-advisory SDK"
    },
    # 4. UAE FinTech Series A verified
    {
        "company_name": "PayFlow Emirates",
        "country": "UAE",
        "state_region": "Dubai",
        "city": "Dubai",
        "primary_industry": "FinTech",
        "business_type": "SaaS Provider",
        "min_order_qty": 5,
        "company_size": "50-200 employees",
        "funding_stage": "Series A",
        "is_verified_business": True,
        "company_bio": "B2B buy-now-pay-later (BNPL) APIs and working capital financing for SMEs in the Gulf region.",
        "core_team_designations": "CEO, Chief Risk Officer, Head of Product",
        "specialties": "B2B BNPL, credit scoring, instant payout infrastructure",
        "product_service_offerings": "checkout integration, risk assessment engine"
    },
    # 5. UAE FinTech Series A verified
    {
        "company_name": "Emaar Ledger",
        "country": "UAE",
        "state_region": "Dubai",
        "city": "Dubai",
        "primary_industry": "FinTech",
        "business_type": "SaaS Provider",
        "min_order_qty": 1,
        "company_size": "50-200 employees",
        "funding_stage": "Series A",
        "is_verified_business": True,
        "company_bio": "Blockchain-based escrow and smart-contract payment solutions for real estate and high-value trade transactions.",
        "core_team_designations": "CEO, Blockchain Architect, Compliance Officer",
        "specialties": "escrow payments, smart contracts, stablecoin settlement",
        "product_service_offerings": "escrow API, contract signing portal"
    },
    # 6. Saudi AgriCorp (Agriculture, Wholesaler)
    {
        "company_name": "Saudi AgriCorp",
        "country": "Saudi Arabia",
        "state_region": "Riyadh",
        "city": "Riyadh",
        "primary_industry": "Agriculture",
        "business_type": "Wholesaler",
        "min_order_qty": 100,
        "company_size": "500+ employees",
        "funding_stage": "Series A",
        "is_verified_business": True,
        "company_bio": "Leading organic fertilizer supplier and bulk grain distributor serving corporate farms in the GCC region.",
        "core_team_designations": "General Manager, Head Agronomist, Logistics Lead",
        "specialties": "bulk supply, organic farming, grain wholesale, fertilizer",
        "product_service_offerings": "bulk organic fertilizers, direct wheat and barley supply"
    },
    # 7. ByteSafe Security (Cybersecurity, SaaS Provider)
    {
        "company_name": "ByteSafe Security",
        "country": "USA",
        "state_region": "Texas",
        "city": "Austin",
        "primary_industry": "Cybersecurity",
        "business_type": "SaaS Provider",
        "min_order_qty": 10,
        "company_size": "50-200 employees",
        "funding_stage": "Series B",
        "is_verified_business": True,
        "company_bio": "Zero-trust network access platform and secure shell credentials management API for cloud architecture.",
        "core_team_designations": "CEO, Chief Security Officer, Devops Lead",
        "specialties": "zero trust, access control, credential rotation, cloud security",
        "product_service_offerings": "ZTNA gateway API, automated credential manager"
    },
    # 8. IndoWeave Textiles (Manufacturing, Manufacturer)
    {
        "company_name": "IndoWeave Textiles",
        "country": "India",
        "state_region": "Gujarat",
        "city": "Ahmedabad",
        "primary_industry": "Manufacturing",
        "business_type": "Manufacturer",
        "min_order_qty": 250,
        "company_size": "200-500 employees",
        "funding_stage": "IPO",
        "is_verified_business": True,
        "company_bio": "High-capacity automated mill manufacturing premium cotton, linen, and custom synthetic B2B textiles.",
        "core_team_designations": "Operations Director, Quality Control, Head of Sales",
        "specialties": "fabric weaving, custom dye, sustainable textiles, raw cotton",
        "product_service_offerings": "wholesale cotton rolls, contract textile weaving"
    },
    # 9. Nippon Precision (Manufacturing, Manufacturer)
    {
        "company_name": "Nippon Precision",
        "country": "Japan",
        "state_region": "Kanto",
        "city": "Tokyo",
        "primary_industry": "Manufacturing",
        "business_type": "Manufacturer",
        "min_order_qty": 500,
        "company_size": "500+ employees",
        "funding_stage": "IPO",
        "is_verified_business": True,
        "company_bio": "Micro-precision CNC machining and high-tolerance steel mold manufacturing for consumer electronics.",
        "core_team_designations": "President, Head Engineer, Chief of Production",
        "specialties": "CNC machining, injection molds, tolerance testing",
        "product_service_offerings": "custom steel molds, precision micro-gears"
    },
    # 10. EuroLogix GmbH (Logistics, Service Provider)
    {
        "company_name": "EuroLogix GmbH",
        "country": "Germany",
        "state_region": "Hamburg",
        "city": "Hamburg",
        "primary_industry": "Logistics",
        "business_type": "Service Provider",
        "min_order_qty": 20,
        "company_size": "200-500 employees",
        "funding_stage": "Series C",
        "is_verified_business": True,
        "company_bio": "Intermodal freight forwarding agency offering warehousing, customs clearance, and cold-chain supply services.",
        "core_team_designations": "Operations VP, Customs Manager, Route Planner",
        "specialties": "sea freight, dry storage, cold chain forwarding, customs broker",
        "product_service_offerings": "container shipping forwarding, chilled cargo logistics"
    },
    # 11. OzAgro Products (Agriculture, Distributor)
    {
        "company_name": "OzAgro Products",
        "country": "Australia",
        "state_region": "NSW",
        "city": "Sydney",
        "primary_industry": "Agriculture",
        "business_type": "Distributor",
        "min_order_qty": 80,
        "company_size": "50-200 employees",
        "funding_stage": "Seed",
        "is_verified_business": False,
        "company_bio": "Distributor of modern automated drip irrigation controllers and precision seeders for retail nursery supply.",
        "core_team_designations": "Founder, Sales Director",
        "specialties": "irrigation supply, seed distribution, greenhouse systems",
        "product_service_offerings": "drip lines, automated watering hubs"
    },
    # 12. Rio Food Group (Agriculture, Wholesaler)
    {
        "company_name": "Rio Food Group",
        "country": "Brazil",
        "state_region": "Sao Paulo",
        "city": "Sao Paulo",
        "primary_industry": "Agriculture",
        "business_type": "Wholesaler",
        "min_order_qty": 150,
        "company_size": "500+ employees",
        "funding_stage": "IPO",
        "is_verified_business": True,
        "company_bio": "Global exporter of green coffee beans and sugarcane molasses representing farming collectives across Brazil.",
        "core_team_designations": "Export VP, Collective Coordinator",
        "specialties": "coffee supply, molasses, trade logistics, agricultural trade",
        "product_service_offerings": "raw arabica coffee beans, organic cane sugar"
    },
    # 13. SingaTech Ventures (SaaS, SaaS Provider)
    {
        "company_name": "SingaTech Ventures",
        "country": "Singapore",
        "state_region": "Central",
        "city": "Singapore",
        "primary_industry": "SaaS",
        "business_type": "SaaS Provider",
        "min_order_qty": 1,
        "company_size": "10-50 employees",
        "funding_stage": "Pre-Seed",
        "is_verified_business": True,
        "company_bio": "AI-driven customer success automation platform that integrates with popular CRM tools.",
        "core_team_designations": "Founder, Product Designer",
        "specialties": "customer retention, chatbot integrations, CRM webhook analytics",
        "product_service_offerings": "SaaS customer success dashboard API"
    },
    # 14. AeroParts Corp (Manufacturing, Manufacturer)
    {
        "company_name": "AeroParts Corp",
        "country": "Canada",
        "state_region": "Quebec",
        "city": "Montreal",
        "primary_industry": "Manufacturing",
        "business_type": "Manufacturer",
        "min_order_qty": 30,
        "company_size": "200-500 employees",
        "funding_stage": "Series B",
        "is_verified_business": True,
        "company_bio": "Aerospace contractor specializing in custom carbon-fiber composite components and heat-resistant hardware.",
        "core_team_designations": "Engineering Director, Quality Controller",
        "specialties": "carbon fiber molding, titanium casting, AS9100 certification",
        "product_service_offerings": "carbon fiber ducts, titanium engine studs"
    },
    # 15. SinoSolar Tech (Manufacturing, Manufacturer)
    {
        "company_name": "SinoSolar Tech",
        "country": "China",
        "state_region": "Shanghai",
        "city": "Shanghai",
        "primary_industry": "Manufacturing",
        "business_type": "Manufacturer",
        "min_order_qty": 1000,
        "company_size": "500+ employees",
        "funding_stage": "IPO",
        "is_verified_business": True,
        "company_bio": "Mass manufacturer of high-efficiency silicon photovoltaic solar cells and solar tracking hardware systems.",
        "core_team_designations": "Production Chief, Solar R&D Director",
        "specialties": "photovoltaic panels, silicon wafers, solar tracker assembly",
        "product_service_offerings": "450W monocrystalline panels, custom framing rails"
    },
    # 16. GigaRobotics (AI Automation, Manufacturer)
    {
        "company_name": "GigaRobotics",
        "country": "USA",
        "state_region": "Massachusetts",
        "city": "Boston",
        "primary_industry": "AI Automation",
        "business_type": "Manufacturer",
        "min_order_qty": 5,
        "company_size": "50-200 employees",
        "funding_stage": "Series A",
        "is_verified_business": True,
        "company_bio": "Manufacturer of autonomous warehouse picking robotic arms and smart sensor conveyor belt units.",
        "core_team_designations": "CEO, Robotics Architect, Sales VP",
        "specialties": "robotics assembly, optical sensors, factory automation",
        "product_service_offerings": "AI-guided robotic arm, conveyor speed controller"
    },
    # 17. AgriGrow Kenya (Agriculture, Wholesaler)
    {
        "company_name": "AgriGrow Kenya",
        "country": "Kenya",
        "state_region": "Nairobi",
        "city": "Nairobi",
        "primary_industry": "Agriculture",
        "business_type": "Wholesaler",
        "min_order_qty": 40,
        "company_size": "10-50 employees",
        "funding_stage": "Seed",
        "is_verified_business": False,
        "company_bio": "Wholesale supplier of drought-resistant seeds and eco-friendly organic pesticides for East African cooperatives.",
        "core_team_designations": "General Manager, Agronomy Specialist",
        "specialties": "organic seed supply, bio-pesticides, sustainable farming",
        "product_service_offerings": "drought-resistant corn seed bags, bio-pesticide drums"
    },
    # 18. Dubai Trade Network (Logistics, Distributor)
    {
        "company_name": "Dubai Trade Network",
        "country": "UAE",
        "state_region": "Dubai",
        "city": "Dubai",
        "primary_industry": "Logistics",
        "business_type": "Distributor",
        "min_order_qty": 15,
        "company_size": "50-200 employees",
        "funding_stage": "Series B",
        "is_verified_business": True,
        "company_bio": "Commercial distribution hub providing customs clearing, palletizing, and regional distribution across UAE ports.",
        "core_team_designations": "Director of Ports, Logistics Lead",
        "specialties": "port coordination, cross-docking, middle-mile transit",
        "product_service_offerings": "cross-docking storage space, regional fleet shipping"
    },
    # 19. Gulf FinTech Labs (FinTech, SaaS Provider)
    {
        "company_name": "Gulf FinTech Labs",
        "country": "Bahrain",
        "state_region": "Manama",
        "city": "Manama",
        "primary_industry": "FinTech",
        "business_type": "SaaS Provider",
        "min_order_qty": 1,
        "company_size": "10-50 employees",
        "funding_stage": "seeding",
        "is_verified_business": True,
        "company_bio": "Multi-currency B2B settlement APIs and currency conversion SDKs for GCC-wide ecommerce integrations.",
        "core_team_designations": "Founder, lead FX developer",
        "specialties": "FX conversion, currency settlement, fintech sandbox",
        "product_service_offerings": "GCC currency exchange API, transaction settlement webhook"
    },
    # 20. London Ad Agency (Marketing, agency)
    {
        "company_name": "London Ad Agency",
        "country": "UK",
        "state_region": "England",
        "city": "London",
        "primary_industry": "Marketing",
        "business_type": "agency",
        "min_order_qty": 1,
        "company_size": "10-50 employees",
        "funding_stage": "Series A",
        "is_verified_business": True,
        "company_bio": "Performance marketing agency specializing in digital ad placements, media buying, and ROI dashboard creation.",
        "core_team_designations": "Creative Director, Head of Ads, Account Manager",
        "specialties": "media buying, digital campaign, analytics, branding",
        "product_service_offerings": "ad campaign execution, visual brand design"
    },
    # 21. Cymru Cyber Lab (Cybersecurity, Service Provider)
    {
        "company_name": "Cymru Cyber Lab",
        "country": "UK",
        "state_region": "Wales",
        "city": "Cardiff",
        "primary_industry": "Cybersecurity",
        "business_type": "Service Provider",
        "min_order_qty": 5,
        "company_size": "10-50 employees",
        "funding_stage": "Seed",
        "is_verified_business": False,
        "company_bio": "Contract cybersecurity firm conducting pen-testing, infrastructure audits, and threat containment services.",
        "core_team_designations": "Lead Security Auditor, Incident Responder",
        "specialties": "pen-testing, code audit, threat containment, GDPR compliance",
        "product_service_offerings": "penetration test report, cyber incident hotline"
    },
    # 22. München Tech (SaaS, SaaS Provider)
    {
        "company_name": "München Tech",
        "country": "Germany",
        "state_region": "Bavaria",
        "city": "Munich",
        "primary_industry": "SaaS",
        "business_type": "SaaS Provider",
        "min_order_qty": 2,
        "company_size": "50-200 employees",
        "funding_stage": "Series A",
        "is_verified_business": True,
        "company_bio": "Automated human resources onboarding tools and employee time logging dashboards tailored for German regulations.",
        "core_team_designations": "CEO, Product Lead, Dev Lead",
        "specialties": "HR software, compliance dashboard, employee tracking",
        "product_service_offerings": "HR portal API, time logger dashboard"
    },
    # 23. Delhi Logistics (Logistics, Wholesaler)
    {
        "company_name": "Delhi Logistics",
        "country": "India",
        "state_region": "Delhi",
        "city": "New Delhi",
        "primary_industry": "Logistics",
        "business_type": "Wholesaler",
        "min_order_qty": 100,
        "company_size": "200-500 employees",
        "funding_stage": "Series B",
        "is_verified_business": True,
        "company_bio": "Bulk supplier of corrugated boxes, industrial bubble wraps, and warehousing pallets for major e-commerce hubs.",
        "core_team_designations": "Sales Director, Operations Head",
        "specialties": "packing materials, corrugated boxes, wooden pallets, tape rolls",
        "product_service_offerings": "custom printed shipping boxes, wholesale cargo pallets"
    },
    # 24. Bangalore Codehouse (SaaS, Service Provider)
    {
        "company_name": "Bangalore Codehouse",
        "country": "India",
        "state_region": "Karnataka",
        "city": "Bengaluru",
        "primary_industry": "SaaS",
        "business_type": "Service Provider",
        "min_order_qty": 1,
        "company_size": "10-50 employees",
        "funding_stage": "Seed",
        "is_verified_business": True,
        "company_bio": "Software development team building custom mobile applications, cloud backend migrations, and UI/UX design wireframes.",
        "core_team_designations": "Technical Director, Lead UI Designer",
        "specialties": "app development, cloud migration, flutter design, custom API",
        "product_service_offerings": "custom mobile app build, cloud database migrations"
    },
    # 25. CapeTown Agritech (Agriculture, SaaS Provider)
    {
        "company_name": "CapeTown Agritech",
        "country": "South Africa",
        "state_region": "Western Cape",
        "city": "Cape Town",
        "primary_industry": "Agriculture",
        "business_type": "SaaS Provider",
        "min_order_qty": 1,
        "company_size": "10-50 employees",
        "funding_stage": "Seed",
        "is_verified_business": False,
        "company_bio": "Soil telemetry sensor hubs and SaaS predictive analysis showing crop hydration levels for regional vineyards.",
        "core_team_designations": "Founder, Soil Scientist",
        "specialties": "soil telemetry, crop prediction, vineyard analytics",
        "product_service_offerings": "IoT soil hydration monitor, vineyard yield forecasting"
    },
    # 26. Quebec Maple Dist (Agriculture, Distributor)
    {
        "company_name": "Quebec Maple Dist",
        "country": "Canada",
        "state_region": "Quebec",
        "city": "Quebec City",
        "primary_industry": "Agriculture",
        "business_type": "Distributor",
        "min_order_qty": 200,
        "company_size": "50-200 employees",
        "funding_stage": "IPO",
        "is_verified_business": True,
        "company_bio": "Bulk distributor of certified organic Canadian maple syrup and granulated maple sugar for confectionery lines.",
        "core_team_designations": "Supply Coordinator, Quality Control",
        "specialties": "maple syrup supply, food wholesale, organic sweeteners",
        "product_service_offerings": "Grade A maple syrup drums, granulated maple sugar sacks"
    },
    # 27. Sydney Scaleups (SaaS, SaaS Provider)
    {
        "company_name": "Sydney Scaleups",
        "country": "Australia",
        "state_region": "NSW",
        "city": "Sydney",
        "primary_industry": "SaaS",
        "business_type": "SaaS Provider",
        "min_order_qty": 1,
        "company_size": "10-50 employees",
        "funding_stage": "Series A",
        "is_verified_business": True,
        "company_bio": "Collaborative project management dashboard software built for design agencies and remote engineering teams.",
        "core_team_designations": "CEO, Lead Frontend Designer",
        "specialties": "project dashboard, agile management, ticket system",
        "product_service_offerings": "SaaS team task manager API"
    },
    # 28. Deccan Chemicals (Manufacturing, Manufacturer)
    {
        "company_name": "Deccan Chemicals",
        "country": "India",
        "state_region": "Telangana",
        "city": "Hyderabad",
        "primary_industry": "Manufacturing",
        "business_type": "Manufacturer",
        "min_order_qty": 500,
        "company_size": "200-500 employees",
        "funding_stage": "IPO",
        "is_verified_business": True,
        "company_bio": "Bulk chemical manufacturer producing industrial cleaning solvents and packaging-grade polymers.",
        "core_team_designations": "Production Chemist, Sales Director",
        "specialties": "industrial solvent, chemical synthesis, polymer sheets",
        "product_service_offerings": "wholesale ethyl alcohol drums, polymer sheet rolls"
    },
    # 29. Lanka Spices Ltd (Agriculture, Wholesaler)
    {
        "company_name": "Lanka Spices Ltd",
        "country": "Sri Lanka",
        "state_region": "Western",
        "city": "Colombo",
        "primary_industry": "Agriculture",
        "business_type": "Wholesaler",
        "min_order_qty": 300,
        "company_size": "200-500 employees",
        "funding_stage": "IPO",
        "is_verified_business": True,
        "company_bio": "Bulk exporter of Ceylon cinnamon, black pepper, and whole cloves directly sourced from local agricultural gardens.",
        "core_team_designations": "Director of Trade, Supply Manager",
        "specialties": "ceylon cinnamon, raw spice wholesaling, exporter",
        "product_service_offerings": "cinnamon quills, organic black pepper bags"
    },
    # 30. Shenzhen LED Co (Manufacturing, Manufacturer)
    {
        "company_name": "Shenzhen LED Co",
        "country": "China",
        "state_region": "Guangdong",
        "city": "Shenzhen",
        "primary_industry": "Manufacturing",
        "business_type": "Manufacturer",
        "min_order_qty": 1000,
        "company_size": "500+ employees",
        "funding_stage": "IPO",
        "is_verified_business": True,
        "company_bio": "High-volume assembly line manufacturing LED light bulbs, dynamic smart display boards, and custom PCBs.",
        "core_team_designations": "Operations Director, PCB Engineer",
        "specialties": "LED lights, PCB design, dynamic display production",
        "product_service_offerings": "LED lighting bulk orders, custom display panels"
    },
    # 31. Nordic Fish Wholesalers (Agriculture, Wholesaler)
    {
        "company_name": "Nordic Fish Wholesalers",
        "country": "Norway",
        "state_region": "Oslo",
        "city": "Oslo",
        "primary_industry": "Agriculture",
        "business_type": "Wholesaler",
        "min_order_qty": 150,
        "company_size": "50-200 employees",
        "funding_stage": "Series A",
        "is_verified_business": True,
        "company_bio": "Wholesale fresh and frozen salmon exporter operating state-of-the-art packaging facilities at Oslo ports.",
        "core_team_designations": "General Manager, Trade Logistics Officer",
        "specialties": "salmon export, cold cargo shipment, sea logistics",
        "product_service_offerings": "fresh salmon boxes, vacuum-sealed frozen salmon"
    },
    # 32. Riyadh Fintech Hub (finance, SaaS Provider)
    {
        "company_name": "Riyadh Fintech Hub",
        "country": "Saudi Arabia",
        "state_region": "Riyadh",
        "city": "Riyadh",
        "primary_industry": "finance",
        "business_type": "SaaS Provider",
        "min_order_qty": 1,
        "company_size": "50-200 employees",
        "funding_stage": "Series B",
        "is_verified_business": True,
        "company_bio": "SaaS core billing software for digital banks and instant transaction processing pipelines for Saudi retail banks.",
        "core_team_designations": "Chief Architect, Compliance Officer",
        "specialties": "core billing, transaction pipeline, digital banking",
        "product_service_offerings": "SaaS core ledger system, instant payment webhook"
    },
    # 33. Bay Area AI (AI Automation, SaaS Provider)
    {
        "company_name": "Bay Area AI",
        "country": "USA",
        "state_region": "California",
        "city": "San Jose",
        "primary_industry": "AI Automation",
        "business_type": "SaaS Provider",
        "min_order_qty": 1,
        "company_size": "10-50 employees",
        "funding_stage": "seeding",
        "is_verified_business": True,
        "company_bio": "Machine learning model deployment API offering serverless deployment and real-time validation for large models.",
        "core_team_designations": "Co-Founders, Principal ML Engineer",
        "specialties": "model deployment, serverless model, real-time validation",
        "product_service_offerings": "ML inference API, custom serverless endpoints"
    },
    # 34. Berlin Green Agri (Agriculture, Service Provider)
    {
        "company_name": "Berlin Green Agri",
        "country": "Germany",
        "state_region": "Berlin",
        "city": "Berlin",
        "primary_industry": "Agriculture",
        "business_type": "Service Provider",
        "min_order_qty": 50,
        "company_size": "10-50 employees",
        "funding_stage": "Seed",
        "is_verified_business": False,
        "company_bio": "Consultancy auditing agricultural soil nutrient content and design planners for sustainable rooftop farming projects.",
        "core_team_designations": "Lead Soil Auditor, Rooftop Designer",
        "specialties": "soil auditing, sustainable agriculture, urban farming planning",
        "product_service_offerings": "soil test reports, custom rooftop farm design"
    },
    # 35. Tokyo Sensor Systems (Manufacturing, Manufacturer)
    {
        "company_name": "Tokyo Sensor Systems",
        "country": "Japan",
        "state_region": "Kanto",
        "city": "Yokohama",
        "primary_industry": "Manufacturing",
        "business_type": "Manufacturer",
        "min_order_qty": 100,
        "company_size": "200-500 employees",
        "funding_stage": "IPO",
        "is_verified_business": True,
        "company_bio": "Optical and thermal laser sensors assembly plant supplying automated robotics builders worldwide.",
        "core_team_designations": "Engineering lead, Global Logistics Manager",
        "specialties": "optical sensor, thermal sensor, high-tolerance hardware",
        "product_service_offerings": "optical distance sensors, thermal array sensors"
    },
    # 36. Cairo LogiHub (Logistics, Service Provider)
    {
        "company_name": "Cairo LogiHub",
        "country": "Egypt",
        "state_region": "Cairo",
        "city": "Cairo",
        "primary_industry": "Logistics",
        "business_type": "Service Provider",
        "min_order_qty": 10,
        "company_size": "50-200 employees",
        "funding_stage": "Series A",
        "is_verified_business": True,
        "company_bio": "Local warehousing agent providing customs brokers and final-mile distribution inside Egyptian markets.",
        "core_team_designations": "Head of Port Logistics, Delivery Coordinator",
        "specialties": "customs clearance, warehousing, final mile transit",
        "product_service_offerings": "warehousing pallet storage, delivery courier fleet"
    },
    # 37. Nairobi Coffee Co (Agriculture, Wholesaler)
    {
        "company_name": "Nairobi Coffee Co",
        "country": "Kenya",
        "state_region": "Nairobi",
        "city": "Nairobi",
        "primary_industry": "Agriculture",
        "business_type": "Wholesaler",
        "min_order_qty": 200,
        "company_size": "50-200 employees",
        "funding_stage": "IPO",
        "is_verified_business": True,
        "company_bio": "Exporter of premium raw AA Arabica coffee beans directly traded from local highland estates.",
        "core_team_designations": "Trade Coordinator, Quality Lead",
        "specialties": "coffee supply, fair trade, agriculture export",
        "product_service_offerings": "raw arabica coffee bags, roasted single origin supply"
    },
    # 38. Austin Marketing Group (Marketing, agency)
    {
        "company_name": "Austin Marketing Group",
        "country": "USA",
        "state_region": "Texas",
        "city": "Austin",
        "primary_industry": "Marketing",
        "business_type": "agency",
        "min_order_qty": 1,
        "company_size": "10-50 employees",
        "funding_stage": "Seed",
        "is_verified_business": True,
        "company_bio": "Marketing agency specializing in search engine optimization, content creation, and lead generation campaigns.",
        "core_team_designations": "CEO, Content Director",
        "specialties": "SEO, lead generation, marketing copy, content design",
        "product_service_offerings": "SEO optimization report, custom marketing blogs"
    },
    # 39. Paris Design Studio (Marketing, agency)
    {
        "company_name": "Paris Design Studio",
        "country": "France",
        "state_region": "Ile-de-France",
        "city": "Paris",
        "primary_industry": "Marketing",
        "business_type": "agency",
        "min_order_qty": 1,
        "company_size": "10-50 employees",
        "funding_stage": "Series A",
        "is_verified_business": True,
        "company_bio": "Premium brand design agency creating digital packaging layouts and custom corporate visual identity sets.",
        "core_team_designations": "Creative Director, Visual Designer",
        "specialties": "brand identity, packaging layouts, corporate styling",
        "product_service_offerings": "visual brand style guides, digital mockups packaging"
    },
    # 40. Abu Dhabi Cloud (SaaS, SaaS Provider)
    {
        "company_name": "Abu Dhabi Cloud",
        "country": "UAE",
        "state_region": "Abu Dhabi",
        "city": "Abu Dhabi",
        "primary_industry": "SaaS",
        "business_type": "SaaS Provider",
        "min_order_qty": 1,
        "company_size": "50-200 employees",
        "funding_stage": "Series B",
        "is_verified_business": True,
        "company_bio": "B2B document sharing and secure virtual data room hosting platform for regional legal audits.",
        "core_team_designations": "Operations Director, Principal Cryptographer",
        "specialties": "virtual data room, file sharing, document encryption",
        "product_service_offerings": "virtual data room subscription, secure upload API"
    },
    # 41. Shams Energy (Manufacturing, Manufacturer)
    {
        "company_name": "Shams Energy",
        "country": "UAE",
        "state_region": "Sharjah",
        "city": "Sharjah",
        "primary_industry": "Manufacturing",
        "business_type": "Manufacturer",
        "min_order_qty": 50,
        "company_size": "50-200 employees",
        "funding_stage": "Series A",
        "is_verified_business": True,
        "company_bio": "Manufacturer of high-tolerance aluminum racking frames and structural mounting clips for commercial solar arrays.",
        "core_team_designations": "Factory Lead, Structural Engineer",
        "specialties": "solar racking, aluminum mounting, commercial frames",
        "product_service_offerings": "aluminum racking rails, solar panel ground mount kits"
    },
    # 42. SafeNet Solutions (Cybersecurity, Service Provider)
    {
        "company_name": "SafeNet Solutions",
        "country": "Saudi Arabia",
        "state_region": "Eastern",
        "city": "Dammam",
        "primary_industry": "Cybersecurity",
        "business_type": "Service Provider",
        "min_order_qty": 1,
        "company_size": "10-50 employees",
        "funding_stage": "Seed",
        "is_verified_business": True,
        "company_bio": "Contract cybersecurity team conducting internal network firewalls configuration and employee security training seminars.",
        "core_team_designations": "CEO, Chief Firewall Specialist",
        "specialties": "firewall setups, network security training, log analytics",
        "product_service_offerings": "firewall configuration check, training seminar packages"
    },
    # 43. Jordan AgriTech (Agriculture, SaaS Provider)
    {
        "company_name": "Jordan AgriTech",
        "country": "Jordan",
        "state_region": "Amman",
        "city": "Amman",
        "primary_industry": "Agriculture",
        "business_type": "SaaS Provider",
        "min_order_qty": 1,
        "company_size": "10-50 employees",
        "funding_stage": "Seed",
        "is_verified_business": False,
        "company_bio": "Smart software mapping regional water well capacity and automated valve control scheduling for large farms.",
        "core_team_designations": "Founder, Hydrogeologist",
        "specialties": "well capacity mapping, dynamic scheduling, automated valve system",
        "product_service_offerings": "water well management dashboard, valve webhook controls"
    },
    # 44. Bayer Automation (AI Automation, Manufacturer)
    {
        "company_name": "Bayer Automation",
        "country": "Germany",
        "state_region": "North Rhine-Westphalia",
        "city": "Cologne",
        "primary_industry": "AI Automation",
        "business_type": "Manufacturer",
        "min_order_qty": 5,
        "company_size": "200-500 employees",
        "funding_stage": "IPO",
        "is_verified_business": True,
        "company_bio": "Assembly line producing computerized conveyor belt sorting systems and laser volumetric scale units.",
        "core_team_designations": "Production Manager, Laser Scale Engineer",
        "specialties": "conveyor sortation, laser scaling, industrial automation",
        "product_service_offerings": "laser scale sorting deck, modular conveyor rollers"
    },
    # 45. Bengal Ironworks (Manufacturing, Manufacturer)
    {
        "company_name": "Bengal Ironworks",
        "country": "India",
        "state_region": "West Bengal",
        "city": "Kolkata",
        "primary_industry": "Manufacturing",
        "business_type": "Manufacturer",
        "min_order_qty": 1000,
        "company_size": "500+ employees",
        "funding_stage": "IPO",
        "is_verified_business": True,
        "company_bio": "High-capacity steel foundry producing cast iron pipes, industrial steel manhole covers, and structural beams.",
        "core_team_designations": "Foundry Director, Quality Controller",
        "specialties": "cast iron pipes, steel structural beams, wholesale metal castings",
        "product_service_offerings": "cast iron pipe joints, heavy-duty steel covers"
    },
    # 46. Seoul Telecom SaaS (SaaS, SaaS Provider)
    {
        "company_name": "Seoul Telecom SaaS",
        "country": "South Korea",
        "state_region": "Seoul",
        "city": "Seoul",
        "primary_industry": "SaaS",
        "business_type": "SaaS Provider",
        "min_order_qty": 10,
        "company_size": "50-200 employees",
        "funding_stage": "Series B",
        "is_verified_business": True,
        "company_bio": "Corporate messaging and virtual customer support ticket assignment API for large telecom carriers.",
        "core_team_designations": "Product VP, Lead Backend Architect",
        "specialties": "telecom dashboard, messaging API, ticket routing",
        "product_service_offerings": "SMS routing portal, customer chat SDK"
    },
    # 47. Milan Fashion Dist (Manufacturing, Distributor)
    {
        "company_name": "Milan Fashion Dist",
        "country": "Italy",
        "state_region": "Lombardy",
        "city": "Milan",
        "primary_industry": "Manufacturing",
        "business_type": "Distributor",
        "min_order_qty": 100,
        "company_size": "200-500 employees",
        "funding_stage": "IPO",
        "is_verified_business": True,
        "company_bio": "Bulk distributor of high-end Italian leather bags, luxury watch cases, and fashion textile accessories.",
        "core_team_designations": "Commercial Director, Brand Liaison",
        "specialties": "leather goods, wholesale accessories, boutique distribution",
        "product_service_offerings": "luxury leather bags wholesale, watch cases bulk"
    },
    # 48. Toronto FinTech Partners (finance, agency)
    {
        "company_name": "Toronto FinTech Partners",
        "country": "Canada",
        "state_region": "Ontario",
        "city": "Toronto",
        "primary_industry": "finance",
        "business_type": "agency",
        "min_order_qty": 1,
        "company_size": "10-50 employees",
        "funding_stage": "seeding",
        "is_verified_business": True,
        "company_bio": "Corporate finance consulting agency structuring debt financing and asset-backed capital funding for scale-ups.",
        "core_team_designations": "General Partner, Investment Analyst",
        "specialties": "debt structuring, capital advisory, scaling loans",
        "product_service_offerings": "debt structuring report, capital brokerage deal"
    },
    # 49. Vikas Pharma (Manufacturing, Manufacturer)
    {
        "company_name": "Vikas Pharma",
        "country": "India",
        "state_region": "Maharashtra",
        "city": "Mumbai",
        "primary_industry": "Manufacturing",
        "business_type": "Manufacturer",
        "min_order_qty": 2000,
        "company_size": "500+ employees",
        "funding_stage": "IPO",
        "is_verified_business": True,
        "company_bio": "Bulk generic pharmaceutical manufacturer producing raw API compounds and wholesale tablet blister packaging.",
        "core_team_designations": "Lead Chemist, Quality Control Lead",
        "specialties": "generic pharma, raw API manufacturing, blister packaging",
        "product_service_offerings": "paracetamol API powder, customized tablet blisters"
    },
    # 50. Dutch Tulip Exports (Agriculture, Distributor)
    {
        "company_name": "Dutch Tulip Exports",
        "country": "Netherlands",
        "state_region": "North Holland",
        "city": "Amsterdam",
        "primary_industry": "Agriculture",
        "business_type": "Distributor",
        "min_order_qty": 500,
        "company_size": "50-200 employees",
        "funding_stage": "IPO",
        "is_verified_business": True,
        "company_bio": "International distributor exporting fresh tulip bulbs and greenhouse flower arrangements in climate cargo.",
        "core_team_designations": "Logistics Coordinator, Nursery Director",
        "specialties": "flower bulb trade, temperature control cargo, global export",
        "product_service_offerings": "wholesale tulip bulbs crate, premium floral display boxes"
    }
]

LOCATIONS = [
    {"country": "UAE", "state_region": "Dubai", "city": "Dubai"},
    {"country": "UAE", "state_region": "Abu Dhabi", "city": "Abu Dhabi"},
    {"country": "USA", "state_region": "California", "city": "San Francisco"},
    {"country": "USA", "state_region": "New York", "city": "New York City"},
    {"country": "USA", "state_region": "Texas", "city": "Austin"},
    {"country": "UK", "state_region": "England", "city": "London"},
    {"country": "Germany", "state_region": "Bavaria", "city": "Munich"},
    {"country": "Germany", "state_region": "Berlin", "city": "Berlin"},
    {"country": "India", "state_region": "Karnataka", "city": "Bangalore"},
    {"country": "India", "state_region": "Maharashtra", "city": "Mumbai"},
    {"country": "Canada", "state_region": "Ontario", "city": "Toronto"},
    {"country": "Canada", "state_region": "Quebec", "city": "Montreal"},
    {"country": "Saudi Arabia", "state_region": "Riyadh", "city": "Riyadh"},
    {"country": "Singapore", "state_region": "Central Region", "city": "Singapore"},
    {"country": "Australia", "state_region": "New South Wales", "city": "Sydney"},
    {"country": "Japan", "state_region": "Tokyo", "city": "Tokyo"},
    {"country": "Egypt", "state_region": "Cairo", "city": "Cairo"},
    {"country": "Kenya", "state_region": "Nairobi", "city": "Nairobi"},
    {"country": "France", "state_region": "Ile-de-France", "city": "Paris"},
    {"country": "Netherlands", "state_region": "North Holland", "city": "Amsterdam"},
    {"country": "Jordan", "state_region": "Amman", "city": "Amman"},
    {"country": "Italy", "state_region": "Lombardy", "city": "Milan"},
]

INDUSTRIES = [
    "FinTech", "SaaS", "Logistics", "Manufacturing", "Marketing",
    "AI Automation", "Cybersecurity", "E-Commerce", "Agriculture",
    "Biotech", "Energy", "Healthcare", "Aerospace", "Chemicals"
]

BUSINESS_TYPES = [
    "SaaS Provider", "Service Provider", "Manufacturer", "Distributor",
    "Wholesaler", "Consultancy", "Agency"
]

COMPANY_SIZES = [
    "1-10 employees", "10-50 employees", "50-200 employees",
    "200-500 employees", "500+ employees"
]

FUNDING_STAGES = [
    "Pre-Seed", "Seed", "Series A", "Series B", "Series C", "IPO"
]

INDUSTRY_TEMPLATES = {
    "FinTech": {
        "bios": [
            "Providing next-generation digital ledger tech and micro-payment APIs for emerging economies.",
            "A secure credit scoring and consumer lending platform utilizing machine learning models.",
            "High-frequency institutional trading software and liquidity aggregation systems.",
            "Cross-border remittance routing and merchant settlement APIs tailored for B2B trade.",
        ],
        "specialties": "digital ledger, micro-payments, credit scoring, algorithmic trading, cross-border remittance, merchant settlement",
        "offerings": "digital ledger API, consumer credit SDK, institutional liquidity pool, cross-border payment gateway"
    },
    "SaaS": {
        "bios": [
            "Cloud-based project management dashboards and collaborative task boards for distributed engineering teams.",
            "Automated human resources recruitment trackers and digital onboarding platforms.",
            "Subscription billing management engines and real-time revenue analytics dashboards.",
            "Customer relationship management platforms featuring automated marketing flows and live chat integrations.",
        ],
        "specialties": "project management, HR automation, billing engine, subscriber analytics, CRM software, marketing automation",
        "offerings": "team collaboration workspace license, HR onboarding portal, API subscription manager, CRM dashboard login"
    },
    "Logistics": {
        "bios": [
            "Cold chain cargo transit and temperature-monitored warehouse storage networks.",
            "Final-mile package delivery orchestration platforms and automated drone shipping fleets.",
            "Port cargo brokerage and customs clearing dispatch services for international importers.",
            "Intermodal cargo route optimization and freight forwarding logistics platforms.",
        ],
        "specialties": "cold cargo transit, temperature storage, final-mile delivery, drone shipping, customs clearing, route optimization",
        "offerings": "refrigerated container lease, automated shipping dispatch, customs clearance package, freight shipping credit"
    },
    "Manufacturing": {
        "bios": [
            "High-tolerance custom injection molding and rapid prototype tool fabricating.",
            "Industrial sensor arrays and automated assembly line controller units.",
            "Precision mechanical components and aluminum framing setups for cleanroom facilities.",
            "Additive manufacturing labs specialized in heavy metal print parts and carbon fiber molds.",
        ],
        "specialties": "injection molding, rapid prototypes, assembly line sensors, precision parts, cleanroom setups, metal 3D printing",
        "offerings": "custom plastic mold tooling, assembly line controller, precision bracket crate, printed titanium gears"
    },
    "Marketing": {
        "bios": [
            "Visual brand identity design and luxury product packaging design services.",
            "Search engine optimization (SEO) automation toolkits and programmatic ad networks.",
            "Influencer marketing booking software and performance metrics dashboard systems.",
            "Content creation agencies generating social video copy and dynamic media packages.",
        ],
        "specialties": "brand identity, packaging design, SEO optimization, programmatic ads, influencer analytics, video marketing",
        "offerings": "corporate branding package, automated SEO audit report, campaign booking subscription, product mockup layout"
    },
    "AI Automation": {
        "bios": [
            "Deep learning neural networks and natural language understanding models for customer support.",
            "Autonomous computer vision systems for quality control in high-speed manufacturing.",
            "Robotic process automation tools capturing screen flows to automate database entry.",
            "Generative AI agent engines designed for drafting legal contracts and matching compliance rules.",
        ],
        "specialties": "neural networks, computer vision, process automation, generative agents, legal AI, compliance matching",
        "offerings": "vision analysis dashboard, document processing API, compliance auditor agent license, custom model training"
    },
    "Cybersecurity": {
        "bios": [
            "Zero-trust network access (ZTNA) clients and virtual private cloud perimeter shields.",
            "Automated penetration testing software and continuous vulnerability scanner systems.",
            "End-point threat detection response (EDR) agents with kernel-level isolation features.",
            "Decentralized identity verification keys and cryptographically secure single-sign-on systems.",
        ],
        "specialties": "zero-trust access, vulnerability scan, threat detection, end-point security, decentralized ID, secure sign-on",
        "offerings": "zero-trust cloud license, network pen-test package, threat sensor licenses, secure SSO authentication API"
    },
    "E-Commerce": {
        "bios": [
            "White-label print-on-demand drop-shipping fulfillment networks with automated routing.",
            "Social commerce checkout links and multi-channel inventory sync engines.",
            "Personalized product recommendation widgets based on user clickstream analytics.",
            "Reverse logistics orchestration portals managing customer returns and warehouse restock.",
        ],
        "specialties": "drop-shipping routing, checkout widgets, multi-channel sync, clickstream personalization, return logistics, restock portals",
        "offerings": "fulfillment dashboard portal, inventory sync API key, smart recommender widget, return tracking portal"
    },
    "Agriculture": {
        "bios": [
            "Greenhouse hydroponic cultivation systems and automated nutrient dosing pumps.",
            "Satellite-guided soil moisture analysis sensors and precision crop yield forecasting.",
            "Fair-trade organic product processing facilities supplying bulk coffee and cacao beans.",
            "Vertically integrated indoor farming shelves featuring LED spectrum tuning arrays.",
        ],
        "specialties": "hydroponic systems, crop forecasting, fair-trade processing, bulk coffee beans, indoor farming, spectrum LEDs",
        "offerings": "hydroponic pump unit, soil analysis report subscription, bulk organic bean sacks, smart LED shelving unit"
    },
    "Biotech": {
        "bios": [
            "CRISPR gene editing reagents and customized cell culture media compounds.",
            "Microfluidic DNA sequencing chipsets and diagnostic assay kit packaging.",
            "High-throughput cellular screening platforms identifying oncology drug candidates.",
            "Synthetic biology fermentation systems producing clean plant-based proteins.",
        ],
        "specialties": "CRISPR gene editing, DNA sequencing, diagnostic assays, high-throughput screen, synthetic biology, plant proteins",
        "offerings": "CRISPR guide RNA design, diagnostic assay cartridge, drug screening run, plant protein powder bulk"
    },
    "Energy": {
        "bios": [
            "High-capacity lithium iron phosphate battery packs for utility-scale grid backup.",
            "Monocrystalline bifacial solar panels and decentralized microgrid control software.",
            "Offshore wind turbine monitoring sensors and predictive rotor maintenance alerts.",
            "Hydrogen fuel cell generator modules for zero-emission commercial backup power.",
        ],
        "specialties": "lithium storage, solar power, microgrid software, wind sensors, hydrogen fuel, backup generators",
        "offerings": "utility battery module, solar panel pallet, wind turbine sensor kit, fuel cell generator unit"
    },
    "Healthcare": {
        "bios": [
            "Remote patient monitoring vitals sensors and secure HIPAA-compliant telehealth portals.",
            "Electronic health record (EHR) database integration software and medical billing checkers.",
            "AI-assisted clinical trial patient recruiting and document matching pipelines.",
            "Wearable medical alert bands with real-time fall detection and GPS location alerts.",
        ],
        "specialties": "patient monitoring, telehealth portals, EHR database, medical billing, clinical trial recruitment, wearable sensors",
        "offerings": "patient tracker device, telehealth portal license, medical billing validator API, wearable alert band package"
    },
    "Aerospace": {
        "bios": [
            "Low-Earth orbit nanosatellite bus units and secure ground station telemetry radios.",
            "Lightweight carbon composite fuselage sections and avionics bracket fabrications.",
            "Precision drone autopilot controllers and telemetry link transmitter modules.",
            "High-thrust electric thruster propulsion drives for satellite orbital adjustments.",
        ],
        "specialties": "nanosatellite units, telemetry radios, carbon composites, avionics brackets, drone autopilot, electric propulsion",
        "offerings": "nanosatellite chassis, composite shell section, autopilot system unit, ion thruster module"
    },
    "Chemicals": {
        "bios": [
            "Specialty bio-degradable industrial solvents and non-toxic metal degreasing fluids.",
            "Advanced polymer resin compounds and high-strength epoxy curing agents.",
            "Agricultural crop protective spray formulations and organic pest barrier chemicals.",
            "Food-grade natural preservative extracts and emulsifying texturing agents.",
        ],
        "specialties": "biodegradable solvents, polymer resins, epoxy curing, crop protectives, natural preservatives, emulsifiers",
        "offerings": "industrial solvent drum, polymer resin pallet, crop protection concentrate, preservative powder wholesale"
    }
}

def generate_dynamic_companies(count: int = 200) -> list:
    import random
    rng = random.Random(42)
    
    prefixes = ["Quantum", "Apex", "Global", "Cyber", "Nova", "Stellar", "Helix", "Synergy", "Vertex", "Nexis", "Alpha", "Omni", "Vanguard", "Delta", "Echo", "Prism", "Matrix", "Stratum", "Beacon", "Cortex", "Aether", "Lumen", "Flux", "Volta", "Krypton", "Obsidian", "Pinnacle", "Titan", "Zodiac", "Solstice"]
    roots = ["Link", "Core", "Sys", "Net", "Logix", "Grid", "Base", "Flow", "Ware", "Scale", "Trust", "Pay", "Space", "Gen", "Bio", "Chem", "Food", "Agri", "Robotics", "Secure", "Logic", "Pulse", "Metrics", "Labs", "Dynamics", "Solutions", "Hive", "Thread", "Node", "Orbit"]
    suffixes = ["Inc", "Solutions", "Technologies", "Group", "Global", "Partners", "Labs", "Systems", "Ventures", "Corp", "Ltd", "International", "Networks", "Enterprises", "Alliance", "Syndicate", "Consortium"]
    
    team_options = [
        "CEO, CTO, Lead Architect",
        "Founder, Managing Director, Head of Engineering",
        "Managing Partner, Chief Risk Officer, Lead Specialist",
        "CEO, Lead Developer, Compliance Lead",
        "Director of Operations, Chief Technologist",
        "General Partner, Chief Commercial Officer, Brand Liaison",
        "Lead Chemist, Quality Assurance Director",
        "CEO, VP of Supply Chain, Logistics Director",
    ]
    
    generated_names = set()
    dynamic_companies = []
    
    existing_names = {c["company_name"] for c in SEED_COMPANIES}
    
    while len(dynamic_companies) < count:
        p = rng.choice(prefixes)
        r = rng.choice(roots)
        s = rng.choice(suffixes)
        name = f"{p} {r} {s}"
        if name in generated_names or name in existing_names:
            continue
        generated_names.add(name)
        
        loc = rng.choice(LOCATIONS)
        ind = rng.choice(INDUSTRIES)
        biz = rng.choice(BUSINESS_TYPES)
        size = rng.choice(COMPANY_SIZES)
        fund = rng.choice(FUNDING_STAGES)
        moq = rng.choice([1, 5, 10, 15, 20, 25, 50, 75, 100, 150, 200, 250, 500, 1000, 2500])
        verified = rng.choice([True, False])
        
        template = INDUSTRY_TEMPLATES[ind]
        bio_template = rng.choice(template["bios"])
        
        company_bio = f"A prominent {biz} in the {ind} sector. {bio_template}"
        specialties = template["specialties"]
        offerings = f"Wholesale {template['offerings']} options, custom {biz.lower()} terms."
        team = rng.choice(team_options)
        
        company = {
            "company_name": name,
            "country": loc["country"],
            "state_region": loc["state_region"],
            "city": loc["city"],
            "primary_industry": ind,
            "business_type": biz,
            "min_order_qty": moq,
            "company_size": size,
            "funding_stage": fund,
            "is_verified_business": verified,
            "company_bio": company_bio,
            "core_team_designations": team,
            "specialties": specialties,
            "product_service_offerings": offerings
        }
        dynamic_companies.append(company)
        
    return dynamic_companies

# Append dynamically generated companies to SEED_COMPANIES
SEED_COMPANIES.extend(generate_dynamic_companies(200))

async def seed_data():
    """
    Creates sample company profiles in MongoDB. Checks uniqueness by company_name
    and pre-computes semantic vector embeddings immediately for testing stability.
    """
    now = datetime.now(timezone.utc)
    for company_data in SEED_COMPANIES:
        # Check if already exists in collection
        existing = await db.companies_collection.find_one({"company_name": company_data["company_name"]})
        if existing:
            print(f"Company '{company_data['company_name']}' already exists, skipping.")
            continue
        
        # Build context & pre-calculate embedding
        context = build_company_context(company_data)
        embedding = generate_embedding(context)
        
        doc = company_data.copy()
        doc["vector_embedding"] = embedding
        doc["created_at"] = now
        doc["updated_at"] = now
        
        await db.companies_collection.insert_one(doc)
        print(f"Seeded: '{company_data['company_name']}' with semantic vector.")

if __name__ == "__main__":
    async def main():
        await connect_to_mongo()
        await seed_data()
        await close_mongo_connection()
    asyncio.run(main())
