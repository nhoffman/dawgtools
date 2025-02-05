-- parameters:
-- epic_pat_id
-- min_date
-- max-date

WITH note AS (
    SELECT
        NOTE_ID, CONTACT_DATE,
        STRING_AGG(CAST(NOTE_TEXT AS NVARCHAR(MAX)), '\n') WITHIN GROUP(ORDER BY LINE ASC) AS NOTE_TEXT
    FROM [uwDAL].[clarity].[HNO_NOTE_TEXT]
    WHERE CONTACT_DATE BETWEEN %(min_date)s AND %(max_date)s
    GROUP BY NOTE_ID, CONTACT_DATE
)
SELECT
    note.NOTE_ID, NOTE_TEXT,
    et.NAME AS encounter_type,
    nti.TITLE,
    info.PAT_ID AS epic_pat_id, note.CONTACT_DATE,
    emp.NAME,
    dep.SPECIALTY
FROM note
JOIN [uwDAL].[clarity].[HNO_INFO] info ON note.NOTE_ID = info.NOTE_ID
JOIN [uwDAL].[clarity].[PAT_ENC] e ON info.PAT_ENC_CSN_ID = e.PAT_ENC_CSN_ID
LEFT JOIN [uwDAL_Clarity].dbo.[ZC_DISP_ENC_TYPE] et ON e.ENC_TYPE_C = et.DISP_ENC_TYPE_C
LEFT JOIN [uwDAL_Clarity].dbo.[ZC_NOTE_TYPE] nt on nt.NOTE_TYPE_C = info.NOTE_TYPE_NOADD_C
LEFT JOIN [uwDAL_Clarity].dbo.[ZC_NOTE_TYPE_IP] nti on nti.TYPE_IP_C = info.IP_NOTE_TYPE_C
LEFT JOIN [uwDAL].clarity.[CLARITY_EMP] emp on emp.USER_ID = info.CURRENT_AUTHOR_ID
LEFT JOIN [uwDAL_Clarity].dbo.[CLARITY_DEP] dep on dep.DEPARTMENT_ID = emp.LGIN_DEPARTMENT_ID
WHERE
info.PAT_ID = %(epic_pat_id)s
