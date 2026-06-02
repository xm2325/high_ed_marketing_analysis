"""Dynamic Streamlit portfolio app using public University of Manchester data snapshots."""
from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from strategy_logic import ConversionScenario, simulate_offer_holder_conversion, make_content_plan, make_access_outreach_scenario
from interactive_tool import make_upload_template, missing_upload_columns, score_and_assign_uploaded_leads

DATA = ROOT / 'data' / 'public_snapshots'
DEMO = ROOT / 'data' / 'demo'

st.set_page_config(page_title='Manchester Recruitment Marketing Strategy Tool', page_icon='🎓', layout='wide')

@st.cache_data(show_spinner=False)
def load_data():
    return {
        'profile': pd.read_csv(DATA/'uom_institution_profile.csv'),
        'signals': pd.read_csv(DATA/'uom_decliner_signals.csv'),
        'funnel': pd.read_csv(DATA/'uom_admissions_funnel.csv'),
        'access': pd.read_csv(DATA/'uom_access_support.csv'),
        'sources': pd.read_csv(DATA/'source_registry.csv'),
        'crm_template': pd.read_csv(DEMO/'synthetic_crm_upload_template.csv'),
    }

def pct(x):
    return f'{100*x:.1f}%'

def pp(x):
    return f'{x:.1f} pp'

def source_note():
    st.info('Public-data sections use committed snapshots from official University of Manchester pages and a UCAS profile. Scenario sliders are planning assumptions, not causal estimates. The CRM sandbox uses synthetic demonstration records only.')

def institution_snapshot(data):
    st.header('1. Manchester public-data snapshot')
    st.write('A public-data starting point for a student recruitment marketing discussion. This page does not use private CRM records.')
    prof=data['profile']
    facts=prof[prof.section=='University facts'].set_index('metric')
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Students', facts.loc['Students','display_value'])
    c2.metric('Staff', facts.loc['Staff','display_value'])
    c3.metric('Alumni', facts.loc['Alumni','display_value'])
    c4.metric('Countries represented', facts.loc['Countries represented','display_value'])
    ucas=prof[prof.section=='UCAS student profile'].copy()
    left,right=st.columns(2)
    with left:
        dom=ucas[ucas.metric.isin(['UK students','EU students','International students'])]
        st.plotly_chart(px.pie(dom,names='metric',values='value',title='Student domicile profile shown by UCAS'),use_container_width=True)
    with right:
        lvl=ucas[ucas.metric.isin(['Undergraduate','Postgraduate'])]
        st.plotly_chart(px.bar(lvl,x='metric',y='value',title='Study level profile shown by UCAS',labels={'value':'Percent'}),use_container_width=True)
    st.success('Public positioning signal: the University states that it was the most popular UK institution for undergraduate applications in the UCAS 2023 cycle. A marketing strategy should therefore focus not only on reach, but on conversion, segment needs, and service quality.')
    source_note()

def evidence_strategy(data):
    st.header('2. Evidence-to-strategy centre')
    st.write('Select an audience and build a concrete communication plan from public Manchester signals.')
    signals=data['signals']
    fee=signals[signals.signal_id=='international_fee_cost'].copy()
    fig=px.bar(fee,x='period',y='value',text='value',title='International decliners citing tuition-fee cost as a main reason',labels={'value':'Percent of international decliners','period':'Cycle'})
    fig.update_traces(texttemplate='%{text:.0f}%',textposition='outside')
    fig.update_yaxes(range=[0,max(55, fee.value.max()+10)])
    st.plotly_chart(fig,use_container_width=True)
    c1,c2,c3=st.columns(3)
    c1.metric('International cost signal, 2024','45%','+9 pp vs 2023')
    c2.metric('Accommodation confidence signal','+11%','2024 vs 2023')
    c3.metric('FSE content signal','Rankings + entry requirements','Higher importance for FSE applicants')

    audience=st.selectbox('Audience',['International undergraduate offer-holders','FSE undergraduate offer-holders','WP Plus / WP Plus PLUS prospective students','All undergraduate offer-holders'])
    st.markdown('**Choose campaign components**')
    cols=st.columns(4)
    include_fee=cols[0].checkbox('Fee-value guidance', value=audience.startswith('International'))
    include_accommodation=cols[1].checkbox('Accommodation reassurance', value=True)
    include_rankings=cols[2].checkbox('Subject value + requirements', value='FSE' in audience)
    include_contextual=cols[3].checkbox('Contextual admissions signposting', value='WP Plus' in audience)
    plan=make_content_plan(audience,include_fee,include_accommodation,include_rankings,include_contextual)
    st.dataframe(plan,use_container_width=True,hide_index=True)
    st.download_button('Download communication plan CSV',plan.to_csv(index=False).encode('utf-8'),'uom_public_data_communication_plan.csv','text/csv')
    st.warning('The public survey page supplies decision signals, not estimated campaign effects. Test message variants with internal CRM data before claiming an uplift.')

def admissions_explorer(data):
    st.header('3. Admissions funnel explorer — real published Manchester data')
    st.write('Explore published application, interview, and offer counts for MBChB Medicine and BDS Dentistry. Use this as an example of stage-specific information design and operational monitoring.')
    df=data['funnel'].copy()
    c1,c2=st.columns(2)
    course=c1.selectbox('Course',sorted(df.course.unique()))
    domicile=c2.selectbox('Domicile',['All','Home','Overseas'])
    view=df[df.course==course].copy()
    if domicile!='All':
        view=view[view.domicile==domicile]
    grouped=view.groupby('entry_year',as_index=False)[['applications','shortlisted_for_interview','offers_made']].sum().sort_values('entry_year')
    long=grouped.melt(id_vars='entry_year',var_name='stage',value_name='count')
    fig=px.line(long,x='entry_year',y='count',color='stage',markers=True,title=f'{course}: published funnel counts')
    years=grouped.entry_year.astype(int).tolist()
    fig.update_xaxes(tickmode='array',tickvals=years,ticktext=[str(y) for y in years])
    st.plotly_chart(fig,use_container_width=True)
    latest=grouped.sort_values('entry_year').iloc[-1]
    a,b,c=st.columns(3)
    a.metric('Applications',f"{int(latest.applications):,}")
    b.metric('Interview rate',pct(latest.shortlisted_for_interview/latest.applications if latest.applications else 0))
    c.metric('Offer / application rate',pct(latest.offers_made/latest.applications if latest.applications else 0))
    detail=view[['course','ucas_code','entry_year','domicile','applications','shortlisted_for_interview','offers_made','interview_rate','offer_per_application_rate','offer_per_interview_rate']].sort_values(['entry_year','domicile'],ascending=[False,True]).copy()
    for col in ['interview_rate','offer_per_application_rate','offer_per_interview_rate']:
        detail[col]=detail[col].map(pct)
    st.dataframe(detail,use_container_width=True,hide_index=True)
    st.download_button('Download filtered published funnel CSV',view.to_csv(index=False).encode('utf-8'),'uom_published_admissions_funnel.csv','text/csv')
    st.warning('The Dentistry page states that historical figures are for information only and should not be used to predict future cycles or determine an applicant strategy. This dashboard uses them for marketing operations examples and stage-specific content planning.')

def conversion_simulator(data):
    st.header('4. Offer-holder conversion scenario tool')
    st.write('Use the public decline signals to frame an internal test plan. Adjust assumptions to estimate the scale of a campaign trial. These are scenario assumptions, not measured Manchester treatment effects.')
    left,right=st.columns(2)
    with left:
        offer_holders=st.number_input('Offer-holder cohort size',min_value=100,max_value=50000,value=5000,step=100)
        baseline=st.slider('Current firm-choice rate',0.0,1.0,0.35,0.01)
        contacted=st.slider('Share receiving targeted sequence',0.0,1.0,0.60,0.05)
    with right:
        fee=st.slider('Assumed uplift from fee-value guidance (percentage points)',0.0,10.0,1.0,0.5)
        accom=st.slider('Assumed uplift from accommodation reassurance (percentage points)',0.0,10.0,1.5,0.5)
        subject=st.slider('Assumed uplift from subject-value / requirement content (percentage points)',0.0,10.0,0.5,0.5)
    out=simulate_offer_holder_conversion(ConversionScenario(int(offer_holders),baseline,contacted,fee,accom,subject))
    a,b,c,d=st.columns(4)
    a.metric('Baseline firms',f"{out['baseline_firms']:.0f}")
    b.metric('Scenario firms',f"{out['scenario_firms']:.0f}")
    c.metric('Additional firms',f"{out['additional_firms']:.0f}")
    d.metric('Scenario firm rate',pct(out['scenario_firm_rate']))
    chart=pd.DataFrame({'scenario':['Baseline','Targeted sequence scenario'],'firm_choices':[out['baseline_firms'],out['scenario_firms']]})
    st.plotly_chart(px.bar(chart,x='scenario',y='firm_choices',text='firm_choices',title='Planning scenario output'),use_container_width=True)
    record=pd.DataFrame([out])
    st.download_button('Download scenario CSV',record.to_csv(index=False).encode('utf-8'),'offer_holder_conversion_scenario.csv','text/csv')
    st.info('Recommended evaluation: randomised or phased message test using internal consent-aware CRM records; report delivered, opened, clicked, webinar registered, firm-choice conversion, and opt-out rates by audience.')

def access_planner(data):
    st.header('5. Contextual access and outreach planner')
    st.write('Manchester publicly states access priorities and support mechanisms. This page turns those into an outreach planning checklist and a scenario tool.')
    access=data['access']
    theme=st.multiselect('Show themes',sorted(access.theme.unique()),default=sorted(access.theme.unique()))
    st.dataframe(access[access.theme.isin(theme)][['theme','item','detail']],use_container_width=True,hide_index=True)
    st.markdown('**Open-day / outreach attendance scenario**')
    c1,c2,c3,c4=st.columns(4)
    seg=c1.number_input('Eligible/prospective segment size',100,50000,3000,100)
    contact=c2.slider('Contacted share',0.0,1.0,0.70,0.05)
    current=c3.slider('Current event-registration rate',0.0,1.0,0.12,0.01)
    uplift=c4.slider('Assumed uplift after clearer signposting (pp)',0.0,15.0,2.0,0.5)
    out=make_access_outreach_scenario(int(seg),contact,current,uplift)
    a,b,c=st.columns(3)
    a.metric('Baseline registrations',f"{out['baseline_attendees']:.0f}")
    b.metric('Scenario registrations',f"{out['scenario_attendees']:.0f}")
    c.metric('Additional registrations',f"{out['additional_attendees']:.0f}")
    st.info('Operational test idea: track eligibility-tool visits, bursary-page visits, travel-support clicks, open-day registrations, completed applications, and conversion by outreach route. Use appropriate governance for personal data.')

def crm_sandbox(data):
    st.header('6. CRM workflow sandbox — synthetic demonstration only')
    st.write('This tab shows how internal CRM records could become a follow-up queue. It uses synthetic records and does not claim to contain Manchester CRM data.')
    template=data['crm_template']
    st.download_button('Download synthetic template CSV',template.to_csv(index=False).encode('utf-8'),'synthetic_crm_upload_template.csv','text/csv')
    uploaded=st.file_uploader('Upload a consent-aware synthetic or authorised CSV',type=['csv'])
    working=pd.read_csv(uploaded) if uploaded is not None else template
    missing=missing_upload_columns(working.columns)
    if missing:
        st.error('Missing required fields: '+', '.join(missing))
        return
    edited=st.data_editor(working,num_rows='dynamic',use_container_width=True,hide_index=True)
    triaged=score_and_assign_uploaded_leads(edited)
    a,b,c=st.columns(3)
    a.metric('Rows triaged',f'{len(triaged):,}')
    b.metric('P1 leads',f"{(triaged.priority_level=='P1').sum():,}")
    c.metric('Data checks',f"{(triaged.priority_level=='Data check').sum():,}")
    st.dataframe(triaged,use_container_width=True,hide_index=True)
    st.download_button('Download action queue',triaged.to_csv(index=False).encode('utf-8'),'synthetic_triaged_action_queue.csv','text/csv')

def sources_limits(data):
    st.header('7. Data sources and limits')
    st.write('The repository commits a reproducible snapshot and a source registry. Refresh the snapshots only after checking the official pages.')
    st.dataframe(data['sources'][['source_id','title','publisher','source_type','used_for','checked_on','url']],use_container_width=True,hide_index=True)
    st.markdown('''
**Limits**

- The public data supports a portfolio demonstration and strategy discussion. It is not a substitute for internal recruitment, marketing-consent, campaign, enquiry, application, offer, firm-choice, and enrolment records.
- Public survey signals are descriptive. They do not estimate the effect of sending a campaign.
- Published Medicine and Dentistry counts illustrate funnel monitoring. They should not be treated as forecasts.
- A production implementation would require data protection review, role-based access, retention rules, audit logs, approved metric definitions, and user training.
''')

def main():
    data=load_data()
    st.title('University of Manchester Recruitment Marketing Strategy Tool — V4')
    st.caption('Dynamic portfolio prototype: official public Manchester data snapshots + clearly labelled planning scenarios + synthetic CRM workflow sandbox.')
    page=st.sidebar.radio('Page',[
        'Manchester Snapshot','Evidence-to-Strategy','Admissions Funnel Explorer','Offer-holder Conversion Scenario','Contextual Access Planner','CRM Workflow Sandbox','Data Sources & Limits'
    ])
    st.sidebar.markdown('---')
    st.sidebar.write('**Portfolio scope**')
    st.sidebar.write('Real public data where available. Planning assumptions are editable. CRM records are synthetic unless authorised data is uploaded.')
    if page=='Manchester Snapshot': institution_snapshot(data)
    elif page=='Evidence-to-Strategy': evidence_strategy(data)
    elif page=='Admissions Funnel Explorer': admissions_explorer(data)
    elif page=='Offer-holder Conversion Scenario': conversion_simulator(data)
    elif page=='Contextual Access Planner': access_planner(data)
    elif page=='CRM Workflow Sandbox': crm_sandbox(data)
    else: sources_limits(data)

if __name__=='__main__':
    main()
