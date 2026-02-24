"""
Management command to populate vocational categories and certifications.

This command creates the complete hierarchical structure for vocational test banks:
- Category: "Vocational"
- Certifications directly under the category (IT, Business, Finance, etc.)

Usage:
    python manage.py populate_vocational
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from catalog.models import Category, Certification


class Command(BaseCommand):
    help = 'Populate vocational categories, subcategories, and certifications'

    def handle(self, *args, **options):
        self.stdout.write('Starting vocational data population...')
        
        # Create or get Vocational category
        vocational_category, created = Category.objects.get_or_create(
            name='Vocational',
            defaults={
                'slug': 'vocational',
                'description': 'Professional certifications and vocational training programs'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created category: {vocational_category.name}'))
        else:
            self.stdout.write(f'Category already exists: {vocational_category.name}')
        
        # Vocational data structure
        # Structure: Category (Vocational) -> Certification (main groups) -> Test Banks (individual certs)
        # Category: Vocational
        # Certification: The main categories (Information Technology & Computer Skills, etc.)
        # Test Banks: Individual certifications (CompTIA A+, etc.) would be test banks linked to certifications
        
        vocational_data = {
            'Information Technology & Computer Skills': {
                'IT Fundamentals / Support': [
                    'CompTIA IT Fundamentals (ITF+)',
                    'CompTIA A+',
                    'CompTIA Network+',
                    'CompTIA Server+',
                    'Google IT Support Professional Certificate',
                    'Cisco CCENT',
                ],
                'Cybersecurity': [
                    'CompTIA Security+',
                    'CompTIA CySA+',
                    'CompTIA PenTest+',
                    'EC-Council CEH (Certified Ethical Hacker)',
                    'EC-Council CHFI',
                    'Offensive Security OSCP',
                    'Cisco CCNA Security',
                    'GIAC Security Essentials (GSEC)',
                ],
                'Cloud & DevOps': [
                    'AWS Cloud Practitioner',
                    'AWS Developer Associate',
                    'AWS Solutions Architect Associate',
                    'Azure Fundamentals (AZ-900)',
                    'Azure Administrator',
                    'Google Cloud Engineer',
                    'Docker Certified Associate',
                    'Kubernetes CKA / CKAD',
                ],
                'Software Development': [
                    'Oracle Java SE Programmer',
                    'Microsoft MTA: Developer',
                    'PCEP / PCAP (Python Certifications)',
                    'JavaScript Developer Certification',
                    'React Developer Certification',
                ],
            },
            'Business, Management & Office Skills': {
                'Project Management': [
                    'PMP (Project Management Professional)',
                    'CAPM (Certified Associate in Project Management)',
                    'PRINCE2 Foundation / Practitioner',
                    'PMI-ACP (Agile)',
                    'Scrum Master (CSM / PSM)',
                ],
                'Business Analysis': [
                    'CBAP (Certified Business Analysis Professional)',
                    'ECBA (Entry Certificate Business Analysis)',
                    'PM-BA Certs (PMI-PBA)',
                ],
                'Quality': [
                    'Six Sigma Yellow Belt',
                    'Six Sigma Green Belt',
                    'Six Sigma Black Belt',
                    'Lean Management Certification',
                ],
                'Office Administration': [
                    'Microsoft Office Specialist (MOS)',
                    'Excel Expert Certification',
                    'Business Writing Certificate',
                    'Office Manager Professional Certificate',
                ],
            },
            'Finance, Accounting & Banking': {
                'Accounting & Finance': [
                    'CMA (Certified Management Accountant)',
                    'CPA (various countries)',
                    'ACCA (Association of Chartered Certified Accountants)',
                    'CIMA',
                    'FRM (Financial Risk Manager)',
                    'Bloomberg Market Concepts (BMC)',
                    'Bookkeeping Certification (AIPB)',
                    'Financial Modeling Certificate (FMVA)',
                ],
            },
            'Marketing, Sales & Customer Service': {
                'Marketing': [
                    'Google Digital Marketing Certificate',
                    'Meta (Facebook) Marketing Professional Certificate',
                    'HubSpot Marketing Certification',
                    'SEO Specialist Certification',
                ],
                'Sales': [
                    'Certified Professional Sales Person (CPSP)',
                    'Sales Management Certification',
                ],
                'Customer Service': [
                    'Customer Service Professional Certification',
                    'CX Professional (CCXP)',
                ],
            },
            'Healthcare & Medical Support': {
                'Clinical Support': [
                    'Certified Nursing Assistant (CNA)',
                    'Patient Care Technician (PCT)',
                    'Emergency Medical Technician (EMT)',
                    'Medical Assistant Certification',
                    'Pharmacy Technician Certification (PTCB)',
                ],
                'Medical Office & Administration': [
                    'Medical Billing & Coding Certification',
                    'Healthcare Administration Certification',
                ],
            },
            'Engineering & Technical Trades': {
                'Electrical & Electronics': [
                    'Electrical Technician Certification',
                    'Electronics Technician Certificate',
                    'Low Voltage Technician Certificate',
                ],
                'Mechanical & Industrial': [
                    'HVAC Technician Certification',
                    'Refrigeration Technician Certification',
                    'AutoCAD Certification',
                    'CNC Machine Operator Certificate',
                ],
                'Construction & Civil Trades': [
                    'OSHA Safety Certifications',
                    'NCCER Construction Certifications',
                    'Civil Construction Supervisor Certificate',
                    'Certified Plumber',
                    'Certified Mason',
                    'Certified Welder',
                ],
            },
            'Creative, Design & Media': {
                'Design & Media': [
                    'Adobe Certified Professional (Photoshop, Illustrator, Premiere)',
                    'Graphic Design Certificate',
                    'UX/UI Design Certificate (Google)',
                    'Animation & Motion Graphics Certificate',
                    'Photography Professional Certification',
                ],
            },
            'Hospitality, Tourism & Events': {
                'Hospitality & Tourism': [
                    'Hotel Management Certificate',
                    'Food Safety Certification (ServSafe)',
                    'Professional Chef Diploma',
                    'Barista Training Certification',
                    'Event Management Certification',
                    'Tour Guide Certification',
                ],
            },
            'Logistics, Supply Chain & Operations': {
                'Supply Chain & Logistics': [
                    'Certified Supply Chain Professional (CSCP)',
                    'Certified Logistics Technician (CLT)',
                    'Warehouse Operations Certificate',
                    'Lean Supply Chain Management',
                    'Procurement Professional Certification (CIPS Levels 1–6)',
                ],
            },
            'Automotive & Transportation': {
                'Automotive': [
                    'Auto Mechanic Certification',
                    'Diesel Technician Certificate',
                    'Automotive Service Excellence (ASE)',
                    'Motorcycle Technician Certificate',
                    'Professional Driving License Specialization (various classes)',
                ],
            },
            'Beauty, Fashion & Personal Care': {
                'Beauty & Fashion': [
                    'Makeup Artist Certification',
                    'Hair Stylist Professional Certification',
                    'Skin Care / Esthetician Certificate',
                    'Spa & Wellness Therapist Certificate',
                    'Fashion Design Certificate',
                    'Nail Technician Certificate',
                ],
            },
            'Education & Language': {
                'Education': [
                    'TESOL / TEFL Certificate for Teachers',
                    'Montessori Teacher Certificate',
                    'Childcare Worker Certificate',
                    'Arabic Language Instructor Certificate',
                    'Special Education Assistant Certification',
                ],
            },
            'Security & Law Enforcement': {
                'Security': [
                    'Security Guard License Certification',
                    'CCTV & Surveillance Operator Certificate',
                    'Private Investigator Certificate',
                    'Fire Safety Officer Certification',
                ],
            },
            'Aviation': {
                'Aviation': [
                    'Cabin Crew Certificate',
                    'IATA Travel & Tourism Certification',
                    'Aircraft Maintenance Technician Certificate',
                    'Flight Dispatch Certificate',
                ],
            },
            'Miscellaneous Vocational Programs': {
                'Miscellaneous': [
                    'Real Estate Agent Certificate',
                    'Property Management Professional Certificate',
                    'Entrepreneurship Small Business Certification',
                    'Call Center Specialist Certificate',
                    'Public Speaking Certification',
                    'Life Coach Certification',
                ],
            },
        }
        
        certification_order = 0
        total_certifications = 0
        
        # Create certifications directly under the Vocational category
        # Structure: 
        # - Category: Vocational
        # - Certification: Main categories (e.g., "Information Technology & Computer Skills")
        # - TestBank: Individual certifications (e.g., "CompTIA A+") - created separately
        for main_category_name, cert_groups_dict in vocational_data.items():
            certification_order += 1
            main_category_slug = slugify(main_category_name)
            
            # Create certification for the main category (e.g., "Information Technology & Computer Skills")
            # Use the main category name as the certification name
            certification, created = Certification.objects.get_or_create(
                category=vocational_category,
                slug=main_category_slug,
                difficulty_level='easy',  # Default difficulty
                defaults={
                    'name': main_category_name,
                    'order': certification_order,
                    'description': f'{main_category_name} vocational programs and certifications'
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created certification: {main_category_name}'))
                total_certifications += 1
            else:
                certification.order = certification_order
                certification.save()
                self.stdout.write(f'  Certification already exists: {main_category_name}')
            
            # Note: The nested groups (e.g., "IT Fundamentals / Support", "Cybersecurity") 
            # and individual certifications (e.g., "CompTIA A+") in certifications_list
            # would be created as TestBanks linked to this Certification, but we don't
            # create test banks automatically - they should be created manually or via admin
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Successfully populated vocational data:\n'
            f'  - 1 Category (Vocational)\n'
            f'  - {total_certifications} Certifications created'
        ))

