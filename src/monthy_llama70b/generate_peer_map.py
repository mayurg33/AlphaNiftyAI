import os
import json
from sentence_transformers import SentenceTransformer, util

# Step 1: Descriptions of all 50 NIFTY companies
company_descriptions = {
    "ADANIENT": "Adani Enterprises is the flagship company of the Adani Group, focused on infrastructure and energy projects.",
    "ADANIPORTS": "Adani Ports and SEZ is India's largest private port operator managing major seaports and logistics services.",
    "APOLLOHOSP": "Apollo Hospitals is a leading healthcare provider in India with a network of multi-specialty hospitals.",
    "ASIANPAINT": "Asian Paints manufactures and sells paints, coatings, and home improvement products in India and globally.",
    "AXISBANK": "Axis Bank is one of India's largest private sector banks offering financial services to retail and corporate clients.",
    "BAJAJ-AUTO": "Bajaj Auto is a major Indian manufacturer of motorcycles, scooters, and auto-rickshaws.",
    "BAJFINANCE": "Bajaj Finance is a non-banking financial company providing consumer and SME loans, insurance, and investments.",
    "BAJAJFINSV": "Bajaj Finserv is a financial services holding company with interests in lending, insurance, and wealth management.",
    "BPCL": "Bharat Petroleum is a state-owned oil and gas company involved in refining and distributing petroleum products.",
    "BHARTIARTL": "Bharti Airtel is a global telecom provider offering mobile, broadband, and DTH services across multiple countries.",
    "BRITANNIA": "Britannia Industries is a food company known for biscuits, dairy, and bakery products in India.",
    "CIPLA": "Cipla is a global pharmaceutical company focused on developing medicines for respiratory, anti-retroviral, and other therapies.",
    "COALINDIA": "Coal India is a government-owned coal mining and production company and the largest in the world.",
    "DIVISLAB": "Divi's Laboratories manufactures active pharmaceutical ingredients and intermediates for global pharma companies.",
    "DRREDDY": "Dr. Reddy's is a pharmaceutical company offering generic drugs, branded formulations, and biotechnology solutions.",
    "EICHERMOT": "Eicher Motors is the parent company of Royal Enfield motorcycles and commercial vehicles manufacturer VE Commercial.",
    "GRASIM": "Grasim Industries operates in cement, textiles, and chemicals, and is part of the Aditya Birla Group.",
    "HCLTECH": "HCL Technologies is a global IT services and consulting company providing digital and software solutions.",
    "HDFCBANK": "HDFC Bank is a leading private bank in India offering retail and wholesale banking, loans, and credit cards.",
    "HDFCLIFE": "HDFC Life is a major life insurance provider in India offering term, endowment, and ULIP products.",
    "HEROMOTOCO": "Hero MotoCorp is the world's largest manufacturer of motorcycles and scooters based in India.",
    "HINDALCO": "Hindalco is a flagship metal company under Aditya Birla Group producing aluminum and copper products.",
    "HINDUNILVR": "Hindustan Unilever is a consumer goods company known for brands in food, home care, and personal care.",
    "ICICIBANK": "ICICI Bank is one of India’s top private banks offering banking and financial services to individuals and businesses.",
    "ITC": "ITC is a diversified Indian conglomerate with businesses in FMCG, hotels, paperboards, packaging, and agri-business.",
    "INDUSINDBK": "IndusInd Bank provides banking and financial services across consumer, corporate, and rural segments.",
    "INFY": "Infosys is a global IT consulting company providing digital services, cloud, and AI-powered business solutions.",
    "JSWSTEEL": "JSW Steel is one of India’s top steel producers involved in manufacturing hot-rolled, cold-rolled, and coated steel products.",
    "KOTAKBANK": "Kotak Mahindra Bank is a major Indian bank offering retail, corporate, and investment banking services.",
    "LTIM": "LTIMindtree is a global technology consulting and digital solutions company formed from LTI and Mindtree merger.",
    "LT": "Larsen & Toubro is a large engineering, construction, and manufacturing conglomerate with global operations.",
    "M&M": "Mahindra & Mahindra is a leading manufacturer of automobiles, tractors, and farm equipment in India.",
    "MARUTI": "Maruti Suzuki is India's largest car manufacturer producing passenger vehicles in multiple segments.",
    "NTPC": "NTPC is a government-owned power utility generating electricity from coal, gas, hydro, and renewable sources.",
    "NESTLEIND": "Nestle India is a food and beverage company known for products in dairy, nutrition, and prepared foods.",
    "ONGC": "Oil and Natural Gas Corporation is a state-run oil and gas exploration company producing crude and natural gas.",
    "POWERGRID": "Power Grid Corporation is a public sector power transmission company operating India's national grid.",
    "RELIANCE": "Reliance Industries is a conglomerate with businesses in energy, petrochemicals, retail, and digital services.",
    "SBILIFE": "SBI Life Insurance is a joint venture life insurer offering a wide range of life and savings plans in India.",
    "SHRIRAMFIN": "Shriram Finance is a NBFC focused on vehicle financing, small business loans, and gold loans.",
    "SBIN": "State Bank of India is the largest public sector bank in India providing a wide range of banking services.",
    "SUNPHARMA": "Sun Pharma is one of India’s biggest pharma companies, manufacturing generic drugs and branded formulations.",
    "TCS": "Tata Consultancy Services is a global IT services and consulting company under the Tata Group.",
    "TATACONSUM": "Tata Consumer Products is a food and beverage company known for Tata Tea, Tata Salt, and coffee brands.",
    "TATAMOTORS": "Tata Motors is a multinational automotive manufacturer producing cars, buses, trucks, and defense vehicles.",
    "TATASTEEL": "Tata Steel is one of the world's top steel producers with operations across India, Europe, and Southeast Asia.",
    "TECHM": "Tech Mahindra is a global IT and business process outsourcing company offering digital transformation services.",
    "TITAN": "Titan Company is a Tata Group firm known for watches, jewelry (Tanishq), and eyewear.",
    "ULTRACEMCO": "UltraTech Cement is the largest cement producer in India and a part of the Aditya Birla Group.",
    "WIPRO": "Wipro is an Indian IT services company offering consulting, cloud, cybersecurity, and software solutions."
}

# Step 2: Embed descriptions using MPNet
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
symbols = list(company_descriptions.keys())
descs = [company_descriptions[s] for s in symbols]
embeddings = model.encode(descs, convert_to_tensor=True)

# Step 3: Compute pairwise similarity
similarity_matrix = util.pytorch_cos_sim(embeddings, embeddings)

# Step 4: Select top 3 most similar peers (excluding self)
peer_map = {}
for i, symbol in enumerate(symbols):
    sim_scores = list(enumerate(similarity_matrix[i]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    top_peers = [symbols[j] for j, _ in sim_scores[1:4]]  # skip self (index 0)
    peer_map[symbol] = top_peers

# Step 5: Save peer map
os.makedirs("data", exist_ok=True)
with open("data/peer_map.json", "w") as f:
    json.dump(peer_map, f, indent=2)

print("[ok] Saved peer_map.json with top 3 peers per company.")
