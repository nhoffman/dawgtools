BEGIN;

with cases as (
  select distinct
    lcdm.CASE_PAT_ID as epic_id,
    pat.PAT_MRN_ID as mrn,
    lcdm.CASE_ID as case_id,
    lci.CASE_NUM as case_num,
    lcdm.CASE_ACCESSION_DTTM accession_dttm,
    str.VALIDATED_RESULT_ID as result_id
    -- case level
    from uwDAL_Clarity.dbo.LAB_CASE_DB_MAIN lcdm
         JOIN uwDAL_Clarity.dbo.LAB_CASE_INFO lci ON lcdm.CASE_ID = lci.REQUISITION_ID
    -- specimen level
         JOIN uwDAL_Clarity.dbo.SPEC_DB_MAIN sdm on lcdm.CASE_ID = sdm.CASE_ID
    -- each case may have multiple specimens with the same result id:
    -- dereplicate these with DISTINCT above
         JOIN uwDAL_Clarity.dbo.SPEC_TEST_REL str on sdm.SPECIMEN_ID = str.SPECIMEN_ID
         JOIN uwDAL_Clarity.dbo.PATIENT pat on lcdm.CASE_PAT_ID = pat.PAT_ID
         {% if case_num %}where lci.CASE_NUM = %(case_num)s
         {% elif mrn %}where pat.PAT_MRN_ID = %(mrn)s
         {% else %}where 1 = 2 {% endif %}
), comps as (
  select
    cases.result_id,
    cc.NAME as comp_name,
    rc.COMP_VERIF_DTTM,
    rv.GROUP_LINE,
    rv.VALUE_LINE,
    rv.MULT_LN_VAL_STG_RAW
    from cases
         JOIN uwDAL_Clarity.dbo.RES_COMPONENTS rc on cases.result_id = rc.RESULT_ID
         JOIN uwDAL_Clarity.dbo.CLARITY_COMPONENT cc on rc.COMPONENT_ID = cc.COMPONENT_ID
         JOIN uwDAL_Clarity.dbo.RES_VAL_PTR_RM ptr ON ptr.RESULT_ID = rc.RESULT_ID
             AND ptr.GROUP_LINE = rc.LINE
         JOIN uwDAL_Clarity.dbo.RES_VAL_DATA_RM rv ON cases.result_id = rv.RESULT_ID
             AND rv.GROUP_LINE = ptr.CMP_MULTILINE_VALUE
), gcomps as (
  select
    comps.result_id,
    max(comps.COMP_VERIF_DTTM) as verif_dttm,
    comps.GROUP_LINE,
    min(comps.comp_name) as comp_name,
    STRING_AGG(CONVERT(VARCHAR(MAX), comps.MULT_LN_VAL_STG_RAW), '\n')
      WITHIN GROUP (ORDER BY comps.GROUP_LINE, comps.VALUE_LINE) AS text
    from comps
   group by comps.result_id, comps.GROUP_LINE
), results as (
  select gcomps.result_id,
         max(gcomps.verif_dttm) as verif_dttm,
         (
           select
             gcomps_inner.comp_name as comp_name,
             gcomps_inner.text
             from gcomps as gcomps_inner
            where gcomps_inner.result_id = gcomps.result_id
            order by gcomps_inner.GROUP_LINE
                     FOR JSON PATH
         ) as reports__json
    from gcomps
   group by gcomps.result_id
)
select
  cases.epic_id,
  cases.mrn,
  cases.case_id,
  cases.case_num,
  cases.accession_dttm,
  cases.result_id,
  results.verif_dttm,
  results.reports__json
  from cases join results on cases.result_id = results.result_id
 order by cases.mrn, cases.accession_dttm;

END;
