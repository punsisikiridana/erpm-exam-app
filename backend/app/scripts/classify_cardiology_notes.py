"""One-off keyword classifier: assigns each Cardiology question a specific
notes.mcqmed.lk sub-section link (Question.notes_url), overriding the
topic-level fallback (the general Cardiology notes page).

This is a best-effort heuristic, not a reliable mapping — mcqmed's own MCQ
data doesn't tag which sub-section a question belongs to (only their notes
site organizes content that way), so this scores keyword hits per question
and picks the best match. Unmatched questions (score 0, or a tie) are left
alone and keep falling back to the topic-level link.

Run with: python -m app.scripts.classify_cardiology_notes [--dry-run] [--topic-id N]
"""

import argparse
import json

from sqlmodel import Session, select

from app.core.database import engine, init_db
from app.models.models import Question

# (section title, notes URL, keywords) — ordered most-specific-first, used
# as the tie-break order when two sections score equally.
SECTIONS: list[tuple[str, str, list[str]]] = [
    (
        "Inherited Connective Tissue Disorders",
        "https://notes.mcqmed.lk/inherited-connective-tissue-disorders-bff9e09639d94530ae8c5b59dae16ed7",
        ["marfan", "ehlers-danlos", "ehlers danlos", "connective tissue disorder"],
    ),
    (
        "Infective endocarditis",
        "https://notes.mcqmed.lk/infective-endocarditis-5e931fb10e074f0a95218ae1dcfe2649",
        ["infective endocarditis", "endocarditis", "vegetation", "janeway", "osler's node", "splinter haemorrhage"],
    ),
    (
        "Rheumatic Fever",
        "https://notes.mcqmed.lk/rheumatic-fever-2ecbd089cf0843e695c053009897b43b",
        ["rheumatic fever", "rheumatic heart", "jones criteria", "erythema marginatum", "sydenham", "chorea"],
    ),
    (
        "Myocarditis and Cardiomyopathy",
        "https://notes.mcqmed.lk/myocarditis-and-cardiomyopathy-e4e97d70e95a4b75b9b2cfdc4b7502e0",
        ["myocarditis", "cardiomyopathy", "hocm", "dilated cardiomyopathy", "hypertrophic cardiomyopathy", "restrictive cardiomyopathy"],
    ),
    (
        "Pericardial diseases",
        "https://notes.mcqmed.lk/pericardial-diseases-7c53c1a21295458f897c02fd200dbbed",
        ["pericarditis", "pericardial effusion", "cardiac tamponade", "tamponade", "constrictive pericarditis", "pericardial rub"],
    ),
    (
        "Pulmonary hypertension and heart disease",
        "https://notes.mcqmed.lk/pulmonary-hypertension-and-heart-disease-d5c331f344b74830bb62389fd265a791",
        ["pulmonary hypertension", "cor pulmonale", "pulmonary artery pressure"],
    ),
    (
        "Cardiac Arrest",
        "https://notes.mcqmed.lk/cardiac-arrest-25ddab9cd4734f65bb0a1740d3565aa9",
        ["cardiac arrest", "cardiopulmonary resuscitation", " cpr ", "defibrillation", "asystole", "pulseless", "basic life support", "advanced life support"],
    ),
    (
        "CHD medicine",
        "https://notes.mcqmed.lk/chd-medicine-4ec70b2376d2400ea0f4108d2f862839",
        [
            "ventricular septal defect", "atrial septal defect", "patent ductus arteriosus", "tetralogy of fallot",
            "coarctation", "transposition of the great", "congenital heart", "eisenmenger", " vsd", " asd", " pda",
            "ebstein", "tricuspid atresia", "truncus arteriosus",
        ],
    ),
    (
        "Valvular Heart Disease CASE",
        "https://notes.mcqmed.lk/valvular-heart-disease-case-f4c861fd1a3e42f096a635f6d60cbad3",
        [
            "mitral stenosis", "mitral regurgitation", "aortic stenosis", "aortic regurgitation",
            "tricuspid regurgitation", "tricuspid stenosis", "pulmonary stenosis", "valvular", "prolapse",
        ],
    ),
    (
        "Acute Coronary Syndrome + CASE",
        "https://notes.mcqmed.lk/acute-coronary-syndrome-case-b60dc90a4d7f4d88b3f8e2f5b7018621",
        [
            "myocardial infarction", "stemi", "nstemi", "unstable angina", "acute coronary syndrome",
            "troponin", "st elevation", "st depression", "thrombolysis", "streptokinase",
            "percutaneous coronary", "coronary angiography", "reperfusion", "angina",
        ],
    ),
    (
        "Arrythmias",
        "https://notes.mcqmed.lk/arrythmias-4a9d8738d30b467294af255d6bf16411",
        [
            "arrhythmia", "atrial fibrillation", "atrial flutter", "supraventricular tachycardia", " svt",
            "ventricular tachycardia", " vt ", "bradycardia", "tachycardia", "heart block", "av block",
            "wolff-parkinson", "wpw", "palpitation", "pacemaker", "long qt", "torsades", "adenosine",
            "amiodarone", "digoxin toxicity", "pulsus",
        ],
    ),
    (
        "Heart failure + CASE",
        "https://notes.mcqmed.lk/heart-failure-case-f7f523f4e47241e3b03c64d3108cdb77",
        [
            "heart failure", "cardiac failure", "pulmonary oedema", "pulmonary edema", "ejection fraction",
            "orthopnoea", "paroxysmal nocturnal dyspnoea", "cardiomegaly", "decompensated", "furosemide",
        ],
    ),
    (
        "Hypertension + CASE",
        "https://notes.mcqmed.lk/hypertension-case-8ad9d1233f704a408daa472a2f8f26b7",
        [
            "hypertension", "hypertensive emergency", "hypertensive crisis", "renal artery stenosis",
            "phaeochromocytoma", "conn syndrome", "hyperaldosteronism", "antihypertensive",
        ],
    ),
    (
        "ECG",
        "https://notes.mcqmed.lk/ecg-ecd1bd72611541ae8b43ac52b59f0737",
        ["axis deviation", "qt interval", "pr interval", "bundle branch block", "u wave", "electrocardiogram"],
    ),
    (
        "Chest Pain CASE",
        "https://notes.mcqmed.lk/chest-pain-case-a2c928759f9f486ea56a1949520eac9e",
        ["chest pain"],
    ),
]


def _text_for(q: Question) -> str:
    parts = json.loads(q.parts_json)
    parts_text = " ".join(p.get("text", "") for p in parts)
    return " ".join(filter(None, [q.stem, parts_text, q.explanation or ""])).lower()


def classify(q: Question) -> tuple[str, str, int] | None:
    text = _text_for(q)
    scored = []
    for title, url, keywords in SECTIONS:
        score = sum(text.count(kw) for kw in keywords)
        if score > 0:
            scored.append((title, url, score))
    if not scored:
        return None
    max_score = max(s[2] for s in scored)
    top = [s for s in scored if s[2] == max_score]
    if len(top) > 1:
        # tie: prefer whichever appears first in SECTIONS (most-specific-first order)
        order = {title: i for i, (title, _, _) in enumerate(SECTIONS)}
        top.sort(key=lambda s: order[s[0]])
    return top[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic-id", type=int, required=True, help="Local Topic.id to classify questions in")
    parser.add_argument("--dry-run", action="store_true", help="Print matches without writing to the database")
    args = parser.parse_args()

    init_db()
    with Session(engine) as session:
        questions = session.exec(select(Question).where(Question.topic_id == args.topic_id)).all()
        matched = unmatched = 0
        for q in questions:
            result = classify(q)
            if result is None:
                unmatched += 1
                print(f"[no match] #{q.id}: {q.stem[:80]}")
                continue
            title, url, score = result
            matched += 1
            print(f"[{title} (score {score})] #{q.id}: {q.stem[:80]}")
            if not args.dry_run:
                q.notes_url = url
                session.add(q)
        if not args.dry_run:
            session.commit()
        print(f"\n{matched} matched, {unmatched} unmatched, out of {len(questions)} total.")
        if args.dry_run:
            print("(dry run — nothing was written)")


if __name__ == "__main__":
    main()
