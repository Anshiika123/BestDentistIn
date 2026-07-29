import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.clinics.models import (
    Clinic,
    ClinicFAQ,
    Dentist,
    Problem,
    Review,
    Treatment,
    VerificationRecord,
)
from apps.content.models import BlogCategory, BlogPost
from apps.locations.models import City, Locality

LOCALITIES = [
    "Civil Lines",
    "IIT Area",
    "Ramnagar",
    "Adarsh Nagar",
    "Ganeshpur",
    "Railway Road",
    "Bhagwanpur Road",
    "Old Roorkee Market",
]

TREATMENTS = [
    {
        "name": "Root Canal Treatment",
        "short_description": "Removes infected pulp to save a badly decayed or infected tooth.",
        "explanation": "A root canal treatment removes infected or damaged pulp from inside a tooth, cleans the "
        "canal, and seals it to prevent further infection — saving the natural tooth instead of extracting it.",
        "symptoms": "Persistent tooth pain, sensitivity to hot/cold that lingers, swelling or tenderness in the gums, "
        "a darkening tooth.",
        "when_to_visit": "Visit a dentist as soon as you notice lingering pain or swelling — delaying treatment "
        "can lead to a spreading infection or tooth loss.",
        "what_to_expect": "The dentist numbs the area, removes the infected pulp, cleans and shapes the canal, "
        "then fills and seals it. A crown is often recommended afterward to protect the tooth. Usually 1-2 visits.",
        "fee_range_min": 2500,
        "fee_range_max": 8000,
    },
    {
        "name": "Braces & Orthodontics",
        "short_description": "Straightens crooked or misaligned teeth using braces or aligners.",
        "explanation": "Braces apply gentle, continuous pressure over time to move teeth into proper alignment, "
        "improving bite and appearance.",
        "symptoms": "Crowded or gapped teeth, difficulty biting/chewing, jaw discomfort from misalignment.",
        "when_to_visit": "Best evaluated early (ages 10-14) but adults can get braces at any age — visit if teeth "
        "are visibly crooked or your bite feels uneven.",
        "what_to_expect": "An initial consultation, X-rays/impressions, then regular adjustment visits every "
        "4-6 weeks over 12-24 months depending on the case.",
        "fee_range_min": 25000,
        "fee_range_max": 80000,
    },
    {
        "name": "Teeth Cleaning & Scaling",
        "short_description": "Removes plaque and tartar buildup for healthier gums.",
        "explanation": "Professional cleaning (scaling) removes hardened plaque and tartar that regular brushing "
        "can't reach, preventing gum disease and bad breath.",
        "symptoms": "Yellowish tartar buildup, bad breath, mild gum bleeding while brushing.",
        "when_to_visit": "Recommended every 6 months as routine preventive care.",
        "what_to_expect": "A quick, mostly painless procedure using ultrasonic tools, usually completed in one visit.",
        "fee_range_min": 500,
        "fee_range_max": 2000,
    },
    {
        "name": "Wisdom Tooth Removal",
        "short_description": "Extraction of impacted or problematic third molars.",
        "explanation": "Wisdom teeth that are impacted, infected, or crowding other teeth are surgically or "
        "simply extracted to relieve pain and prevent complications.",
        "symptoms": "Pain at the back of the jaw, swelling, difficulty opening the mouth, gum tenderness near the molars.",
        "when_to_visit": "See a dentist promptly if you have persistent jaw pain or swelling near your back teeth.",
        "what_to_expect": "Local anesthesia, extraction (simple or surgical depending on impaction), and a few "
        "days of recovery with soft-food diet.",
        "fee_range_min": 1500,
        "fee_range_max": 6000,
    },
    {
        "name": "Child Dentistry",
        "short_description": "Gentle dental care tailored for infants, children, and teens.",
        "explanation": "Pediatric dental care focuses on preventive checkups, cavity treatment, and healthy habit "
        "building for growing teeth.",
        "symptoms": "Tooth decay in baby teeth, thumb-sucking related bite issues, complaints of tooth pain in children.",
        "when_to_visit": "First dental visit by age 1, then every 6 months for checkups.",
        "what_to_expect": "A child-friendly, low-stress visit focused on prevention, with treatment only when necessary.",
        "fee_range_min": 500,
        "fee_range_max": 5000,
    },
    {
        "name": "Gum Treatment",
        "short_description": "Treats gum disease (gingivitis/periodontitis) to protect teeth and gums.",
        "explanation": "Gum treatment ranges from deep cleaning (scaling and root planing) to more advanced "
        "periodontal therapy for infected or receding gums.",
        "symptoms": "Bleeding gums, swelling, bad breath, receding gum line, loose teeth.",
        "when_to_visit": "See a dentist if gums bleed regularly or feel swollen/tender for more than a week.",
        "what_to_expect": "Deep cleaning below the gumline, possibly over multiple visits, with follow-up care instructions.",
        "fee_range_min": 1500,
        "fee_range_max": 10000,
    },
    {
        "name": "Dental Fillings",
        "short_description": "Repairs cavities caused by tooth decay.",
        "explanation": "A filling removes decayed tooth material and fills the space with a tooth-colored or "
        "metal material to restore shape and function.",
        "symptoms": "Visible holes or dark spots on teeth, sensitivity to sweet or cold foods, mild pain while chewing.",
        "when_to_visit": "As soon as a cavity is noticed or suspected, to prevent it from reaching the nerve.",
        "what_to_expect": "A single-visit procedure: numbing, decay removal, and filling placement.",
        "fee_range_min": 800,
        "fee_range_max": 3500,
    },
    {
        "name": "Dental Crowns",
        "short_description": "Caps a damaged or weakened tooth to restore strength and shape.",
        "explanation": "A crown is a custom cap placed over a tooth to restore its size, strength, and appearance "
        "after major decay, a root canal, or a fracture.",
        "symptoms": "A cracked or heavily filled tooth, a tooth that feels weak or is at risk of breaking.",
        "when_to_visit": "When a dentist identifies a tooth too damaged for a regular filling.",
        "what_to_expect": "Tooth preparation, an impression or scan, a temporary crown, then a final crown fitted "
        "over 1-2 visits.",
        "fee_range_min": 4000,
        "fee_range_max": 15000,
    },
]

PROBLEMS = [
    {
        "name": "Tooth Pain",
        "short_description": "Sharp, dull, or throbbing pain in or around a tooth.",
        "symptom_explanation": "Tooth pain can range from a mild ache to sharp, throbbing pain, sometimes worse "
        "with hot, cold, or sweet foods.",
        "possible_causes": "Cavities, cracked teeth, gum infection, exposed roots, or an abscess. This is not a "
        "diagnosis — a dentist needs to examine the tooth to determine the exact cause.",
        "when_urgent_care_needed": "Seek urgent care if pain is severe, accompanied by facial swelling, fever, "
        "or difficulty swallowing.",
    },
    {
        "name": "Bleeding Gums",
        "short_description": "Gums that bleed during brushing, flossing, or spontaneously.",
        "symptom_explanation": "Gums may appear red, swollen, and bleed when brushed or flossed.",
        "possible_causes": "Plaque buildup, gingivitis, aggressive brushing, or early periodontal disease. "
        "This is general information, not a diagnosis.",
        "when_urgent_care_needed": "See a dentist if bleeding persists for more than a week or is accompanied "
        "by loose teeth.",
    },
    {
        "name": "Tooth Sensitivity",
        "short_description": "Discomfort when eating or drinking something hot, cold, or sweet.",
        "symptom_explanation": "A sharp, temporary pain triggered by temperature or sweet foods touching exposed "
        "dentin or nerve endings.",
        "possible_causes": "Worn enamel, receding gums, cavities, or a cracked tooth.",
        "when_urgent_care_needed": "If sensitivity is sudden and severe or paired with visible tooth damage, see "
        "a dentist promptly.",
    },
    {
        "name": "Wisdom Tooth Pain",
        "short_description": "Pain at the back of the jaw from erupting or impacted wisdom teeth.",
        "symptom_explanation": "Dull to sharp pain near the back molars, sometimes with swelling or difficulty "
        "opening the mouth.",
        "possible_causes": "Impacted wisdom teeth, infection around a partially erupted tooth, or crowding.",
        "when_urgent_care_needed": "Seek care if there's facial swelling, fever, or you cannot open your mouth fully.",
    },
    {
        "name": "Bad Breath",
        "short_description": "Persistent unpleasant breath odor.",
        "symptom_explanation": "Ongoing bad breath not resolved by regular brushing and mouthwash.",
        "possible_causes": "Plaque/tartar buildup, gum disease, dry mouth, or tooth decay.",
        "when_urgent_care_needed": "If bad breath persists despite good oral hygiene, a dental checkup can "
        "identify the underlying cause.",
    },
    {
        "name": "Gum Swelling",
        "short_description": "Puffy, tender, or inflamed gums.",
        "symptom_explanation": "Gums may look enlarged, feel tender to touch, and sometimes appear red or shiny.",
        "possible_causes": "Infection, gum disease, an abscess, or irritation from food debris.",
        "when_urgent_care_needed": "Seek prompt care if swelling is accompanied by fever, facial swelling, or "
        "severe pain — this can indicate a spreading infection.",
    },
    {
        "name": "Cavity",
        "short_description": "A decayed area or hole in the tooth surface.",
        "symptom_explanation": "May appear as a visible dark spot or hole, sometimes with sensitivity or pain.",
        "possible_causes": "Bacterial plaque breaking down tooth enamel over time, often linked to sugar intake "
        "and inconsistent brushing.",
        "when_urgent_care_needed": "See a dentist as soon as a cavity is suspected, before it reaches the nerve.",
    },
    {
        "name": "Broken Tooth",
        "short_description": "A chipped, cracked, or fractured tooth.",
        "symptom_explanation": "Visible chip or crack, sometimes with sharp edges, pain when chewing, or sensitivity.",
        "possible_causes": "Trauma, biting hard objects, large old fillings, or untreated decay weakening the tooth.",
        "when_urgent_care_needed": "Seek care promptly, especially if there's pain, bleeding, or a visible nerve exposure.",
    },
]

FIRST_NAMES = [
    "Anil", "Sunita", "Rajesh", "Priya", "Vikram", "Neha", "Sanjay", "Kavita",
    "Manoj", "Ritu", "Ashok", "Pooja", "Deepak", "Anjali", "Rakesh", "Shalini",
    "Vivek", "Meena", "Amit", "Sarika", "Naveen", "Divya", "Suresh", "Kiran",
]
LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Rastogi", "Chauhan", "Tyagi", "Saini", "Malhotra",
    "Agarwal", "Bhatia", "Kapoor", "Rana", "Rawat", "Joshi", "Bansal", "Mittal",
]
QUALIFICATIONS = [
    "BDS", "BDS, MDS (Orthodontics)", "BDS, MDS (Oral Surgery)",
    "BDS, MDS (Periodontics)", "BDS, MDS (Prosthodontics)", "BDS, MDS (Endodontics)",
    "BDS, MDS (Pediatric Dentistry)",
]
CLINIC_SUFFIXES = ["Dental Care", "Dental Clinic", "Dental Studio", "Multispeciality Dental Clinic", "Smile Care Dental"]

BLOG_CATEGORIES = ["Teeth Pain", "Oral Hygiene", "Root Canal", "Braces", "Kids Dentistry"]

BLOG_POSTS = [
    ("5 Early Signs of Tooth Decay You Shouldn't Ignore", "Teeth Pain"),
    ("Why Does My Tooth Hurt When I Drink Something Cold?", "Teeth Pain"),
    ("A Simple Daily Oral Hygiene Routine That Actually Works", "Oral Hygiene"),
    ("Flossing 101: How to Do It Right", "Oral Hygiene"),
    ("Root Canal Myths, Debunked", "Root Canal"),
    ("What to Expect Before, During, and After a Root Canal", "Root Canal"),
    ("Braces vs Clear Aligners: Which Is Right for You?", "Braces"),
    ("How Long Does Orthodontic Treatment Usually Take?", "Braces"),
    ("First Dental Visit: A Guide for Parents in Roorkee", "Kids Dentistry"),
    ("Helping Kids Overcome Fear of the Dentist", "Kids Dentistry"),
]


class Command(BaseCommand):
    help = "Seed realistic mock data for BestDentistIn — Roorkee only."

    def add_arguments(self, parser):
        parser.add_argument("--clinics", type=int, default=40, help="Number of clinics to generate (30-50).")
        parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")

    def handle(self, *args, **options):
        random.seed(options["seed"])
        num_clinics = max(30, min(50, options["clinics"]))

        city = self._create_city()
        localities = self._create_localities(city)
        treatments = self._create_treatments(city)
        problems = self._create_problems(city, treatments)
        clinics = self._create_clinics(city, localities, treatments, problems, num_clinics)
        self._create_faqs(city, localities, treatments, problems)
        self._create_blog(treatments, problems)

        self.stdout.write(self.style.SUCCESS(
            f"Seeded: 1 city, {len(localities)} localities, {len(treatments)} treatments, "
            f"{len(problems)} problems, {len(clinics)} clinics."
        ))

    def _create_city(self):
        city, _ = City.objects.update_or_create(
            slug="roorkee",
            defaults={
                "name": "Roorkee",
                "state": "Uttarakhand",
                "meta_title": "Best Dentists in Roorkee | BestDentistIn",
                "meta_description": "Find verified dentists in Roorkee. Compare clinics by locality and "
                "treatment, and contact them instantly on WhatsApp or call.",
                "intro_content": "Roorkee is home to dozens of dental clinics spread across localities like "
                "Civil Lines, IIT Area, and Ramnagar. Whether you need a routine cleaning or a root canal, "
                "BestDentistIn helps you compare verified clinics and reach out directly — no waiting rooms, "
                "no call centers.",
                "is_active": True,
            },
        )
        return city

    def _create_localities(self, city):
        localities = []
        for name in LOCALITIES:
            locality, _ = Locality.objects.update_or_create(
                city=city,
                slug=slugify(name),
                defaults={
                    "name": name,
                    "meta_description": f"Verified dentists and dental clinics in {name}, Roorkee.",
                    "intro_content": f"{name} is a well-connected part of Roorkee with several dental clinics "
                    "offering routine and specialized treatments close to home.",
                    "is_active": True,
                },
            )
            localities.append(locality)
        return localities

    def _create_treatments(self, city):
        treatments = []
        for t in TREATMENTS:
            obj, _ = Treatment.objects.update_or_create(
                city=city,
                slug=slugify(t["name"]),
                defaults={
                    "name": t["name"],
                    "short_description": t["short_description"],
                    "explanation": t["explanation"],
                    "symptoms": t["symptoms"],
                    "when_to_visit": t["when_to_visit"],
                    "what_to_expect": t["what_to_expect"],
                    "fee_range_min": t["fee_range_min"],
                    "fee_range_max": t["fee_range_max"],
                    "is_active": True,
                },
            )
            treatments.append(obj)
        return treatments

    def _create_problems(self, city, treatments):
        problems = []
        treatment_by_slug = {t.slug: t for t in treatments}
        problem_treatment_map = {
            "Tooth Pain": ["root-canal-treatment", "dental-fillings"],
            "Bleeding Gums": ["gum-treatment", "teeth-cleaning-scaling"],
            "Tooth Sensitivity": ["dental-fillings", "gum-treatment"],
            "Wisdom Tooth Pain": ["wisdom-tooth-removal"],
            "Bad Breath": ["teeth-cleaning-scaling", "gum-treatment"],
            "Gum Swelling": ["gum-treatment"],
            "Cavity": ["dental-fillings", "root-canal-treatment"],
            "Broken Tooth": ["dental-crowns", "dental-fillings"],
        }
        for p in PROBLEMS:
            obj, _ = Problem.objects.update_or_create(
                city=city,
                slug=slugify(p["name"]),
                defaults={
                    "name": p["name"],
                    "short_description": p["short_description"],
                    "symptom_explanation": p["symptom_explanation"],
                    "possible_causes": p["possible_causes"],
                    "when_urgent_care_needed": p["when_urgent_care_needed"],
                    "is_active": True,
                },
            )
            related_slugs = problem_treatment_map.get(p["name"], [])
            related = [treatment_by_slug[s] for s in related_slugs if s in treatment_by_slug]
            if related:
                obj.suggested_treatment_categories.set(related)
            problems.append(obj)
        return problems

    def _create_clinics(self, city, localities, treatments, problems, num_clinics):
        clinics = []
        used_names = set()
        for i in range(num_clinics):
            last = random.choice(LAST_NAMES)
            suffix = random.choice(CLINIC_SUFFIXES)
            base_name = f"Dr. {last} {suffix}"
            name = base_name
            n = 2
            while name in used_names:
                name = f"{base_name} {n}"
                n += 1
            used_names.add(name)

            slug = slugify(f"{name}-roorkee")
            locality = random.choice(localities)
            phone_local = f"01332-{random.randint(200000, 299999)}"
            whatsapp = f"91{random.randint(7000000000, 9999999999)}"

            clinic, _ = Clinic.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "city": city,
                    "locality": locality,
                    "address": f"{random.randint(1, 200)}, {locality.name}, Roorkee, Uttarakhand",
                    "phone_number": phone_local,
                    "whatsapp_number": whatsapp,
                    "timings": random.choice([
                        "Mon-Sat 9:00 AM - 7:00 PM",
                        "Mon-Sat 10:00 AM - 8:00 PM, Sun 10:00 AM - 2:00 PM",
                        "Mon-Sun 9:30 AM - 6:30 PM",
                        "Tue-Sun 11:00 AM - 8:00 PM",
                    ]),
                    "consultation_fee": random.choice([200, 300, 500, 0, None]),
                    "about": f"{name} provides comprehensive dental care in {locality.name}, Roorkee, focused on "
                    "comfortable, modern treatment for the whole family.",
                    "meta_description": f"{name} — dental clinic in {locality.name}, Roorkee. View treatments, "
                    "timings, and contact directly on WhatsApp or call.",
                    "is_active": True,
                    "is_featured": i < 6,
                },
            )

            clinic_treatments = random.sample(treatments, k=random.randint(3, 6))
            clinic.treatments.set(clinic_treatments)
            clinic.problems.set(random.sample(problems, k=random.randint(2, 5)))

            Dentist.objects.filter(clinic=clinic).delete()
            Dentist.objects.create(
                clinic=clinic,
                name=f"{random.choice(FIRST_NAMES)} {last}",
                qualification=random.choice(QUALIFICATIONS),
                experience_years=random.randint(3, 25),
                bio=f"Dr. {last} has been practicing dentistry in Roorkee, focusing on patient comfort and "
                "modern treatment techniques.",
                is_primary=True,
            )

            is_verified = random.random() < 0.6
            VerificationRecord.objects.filter(clinic=clinic).delete()
            VerificationRecord.objects.create(
                clinic=clinic,
                is_verified=is_verified,
                verification_source=random.choice(VerificationRecord.Source.values),
                last_verified_at=timezone.now() - timedelta(days=random.randint(0, 400) if not is_verified else random.randint(0, 150)),
                phone_confirmed=is_verified,
                timings_confirmed=is_verified,
                notes="Verified via phone call and Google Business Profile." if is_verified else "Pending verification.",
            )

            if random.random() < 0.4:
                Review.objects.filter(clinic=clinic).delete()
                for _ in range(random.randint(1, 3)):
                    Review.objects.create(
                        clinic=clinic,
                        author_name=random.choice(FIRST_NAMES),
                        rating=random.choice([4, 4, 5, 5, 5, 3]),
                        comment="Good experience, clean clinic and friendly staff.",
                    )

            clinics.append(clinic)
        return clinics

    def _create_faqs(self, city, localities, treatments, problems):
        ClinicFAQ.objects.filter(clinic__isnull=True).delete()
        ClinicFAQ.objects.create(
            city=city,
            question="How do I book an appointment with a dentist in Roorkee?",
            answer="Browse clinics on this page, then tap WhatsApp or Call on any clinic card to contact them "
            "directly — appointments are confirmed by the clinic, not by BestDentistIn.",
            order=1,
        )
        ClinicFAQ.objects.create(
            city=city,
            question="What does the 'Verified' badge mean?",
            answer="A verified clinic has had its phone number, timings, and profile details confirmed by our "
            "team within the last few months.",
            order=2,
        )
        for locality in localities[:3]:
            ClinicFAQ.objects.create(
                locality=locality,
                question=f"Are there dentists open on weekends in {locality.name}?",
                answer=f"Several clinics in {locality.name} are open on Sundays or have extended weekend hours — "
                "check each clinic's timings on their profile page.",
                order=1,
            )
        for treatment in treatments:
            ClinicFAQ.objects.create(
                treatment=treatment,
                question=f"How much does {treatment.name.lower()} cost in Roorkee?",
                answer=f"Estimated fees range from ₹{treatment.fee_range_min} to ₹{treatment.fee_range_max}, "
                "though the exact cost depends on the clinic and case complexity. Confirm directly with the clinic.",
                order=1,
            )
        for problem in problems:
            ClinicFAQ.objects.create(
                problem=problem,
                question=f"Is {problem.name.lower()} always a dental emergency?",
                answer="Not always, but persistent or severe symptoms should be checked by a dentist promptly to "
                "prevent the issue from worsening.",
                order=1,
            )

    def _create_blog(self, treatments, problems):
        treatment_by_slug = {t.slug: t for t in treatments}
        problem_by_slug = {p.slug: p for p in problems}

        # Drives the internal-linking engine (apps.seo.linking): treatment/problem
        # pages surface posts from these categories, and posts link back to them.
        category_link_map = {
            "Teeth Pain": {
                "treatments": ["root-canal-treatment", "dental-fillings"],
                "problems": ["tooth-pain", "cavity", "broken-tooth"],
            },
            "Oral Hygiene": {
                "treatments": ["teeth-cleaning-scaling"],
                "problems": ["bad-breath", "bleeding-gums"],
            },
            "Root Canal": {
                "treatments": ["root-canal-treatment"],
                "problems": ["tooth-pain", "cavity"],
            },
            "Braces": {
                "treatments": ["braces-orthodontics"],
                "problems": [],
            },
            "Kids Dentistry": {
                "treatments": ["child-dentistry"],
                "problems": [],
            },
        }

        categories = {}
        for name in BLOG_CATEGORIES:
            cat, _ = BlogCategory.objects.update_or_create(slug=slugify(name), defaults={"name": name})
            links = category_link_map.get(name, {})
            cat.treatments.set([treatment_by_slug[s] for s in links.get("treatments", []) if s in treatment_by_slug])
            cat.problems.set([problem_by_slug[s] for s in links.get("problems", []) if s in problem_by_slug])
            categories[name] = cat

        for title, cat_name in BLOG_POSTS:
            BlogPost.objects.update_or_create(
                slug=slugify(title),
                defaults={
                    "title": title,
                    "category": categories[cat_name],
                    "excerpt": f"A practical guide on {title.lower()}.",
                    "body": f"{title}\n\nThis is placeholder Phase 1 content. Replace with a full article covering "
                    "practical, locally relevant dental health guidance for readers in Roorkee.\n\n"
                    "This content is informational only and is not a substitute for professional dental advice.",
                    "author_name": "BestDentistIn Team",
                    "is_published": True,
                    "published_at": timezone.now() - timedelta(days=random.randint(0, 60)),
                },
            )
