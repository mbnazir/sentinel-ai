<?php

/**
 * Reference-only Yii 1.1 controller for Sentinel's read-only Quartz export.
 *
 * Adapt authentication/route registration to Quartz standards before production.
 * Never expose these endpoints without service authentication and network controls.
 */
class SentinelController extends Controller
{
    const MAX_LIMIT = 1000;

    public function filters()
    {
        return array();
    }

    protected function beforeAction($action)
    {
        $expected = isset(Yii::app()->params['sentinelApiToken'])
            ? Yii::app()->params['sentinelApiToken']
            : null;

        $header = isset($_SERVER['HTTP_AUTHORIZATION'])
            ? $_SERVER['HTTP_AUTHORIZATION']
            : '';

        if (!$expected || $header !== 'Bearer ' . $expected) {
            $this->json(array('error' => 'Unauthorized'), 401);
            return false;
        }

        return parent::beforeAction($action);
    }

    public function actionLoginSessions()
    {
        $from = Yii::app()->request->getQuery('shift_date_from');
        $to = Yii::app()->request->getQuery('shift_date_to');
        $cursor = Yii::app()->request->getQuery('cursor', 0);
        $limit = min(
            max((int)Yii::app()->request->getQuery('limit', 500), 1),
            self::MAX_LIMIT
        );

        if (!$this->validDate($from) || !$this->validDate($to)) {
            return $this->json(array('error' => 'shift_date_from/to must be YYYY-MM-DD'), 400);
        }

        $criteria = new CDbCriteria();
        $criteria->addBetweenCondition('shift_date', $from, $to);
        $criteria->addCondition('id > :cursor');
        $criteria->params[':cursor'] = (int)$cursor;
        $criteria->order = 'id ASC';
        $criteria->limit = $limit;

        $rows = LoginSessions::model()->findAll($criteria);
        $items = array();

        foreach ($rows as $row) {
            $items[] = array(
                'id' => (string)$row->id,
                'agent_id' => $row->agent_id,
                'supervisor_id' => $row->supervisor_id,
                'shift_date' => $row->shift_date,
                'start_date' => $this->iso($row->start_date),
                'end_date' => $this->iso($row->end_date),
                'status_id' => $row->status_id,
                'dispute_reason_id' => $row->dispute_reason_id,
                'dispute_state' => $row->dispute_state,
                'supervisor_status_id' => $row->supervisor_status_id,
                'ready_for_payroll' => (int)$row->ready_for_payroll,
                'payroll_adjusted' => (int)$row->payroll_adjusted,
                'payroll_adjust_dt' => $this->iso($row->payroll_adjust_dt),
                'session_added_by' => $row->session_added_by,
                'add_session_reason_id' => $row->add_session_reason_id,
                'agent_action_timestamp' => $this->iso($row->agent_action_timestamp),
                'supervisor_action_timestamp' => $this->iso($row->supervisor_action_timestamp),
                'manager_action_timestamp' => $this->iso($row->manager_action_timestamp),
                'multiple_logins' => (int)$row->multiple_logins,
                'agent_ip' => $row->agent_ip,
                'machine_hostname' => $row->machine_hostname,
                'primary_campaign_id' => $row->primary_campaign_id,
                'primary_campaign_name' => $row->primary_campaign_name,
                'primary_client_id' => $row->primary_client_id,
                'primary_client_name' => $row->primary_client_name,
                'data_source_id' => $row->data_source_id,
                'session_source' => $row->session_source,
                'resolve_dispute_by' => $row->resolve_dispute_by,
                'closed_by' => $row->closed_by,
                'closed_by_type' => $row->closed_by_type,
                'overtime' => $row->overtime,
                'regular_hour' => $row->regular_hour,
                // Add manager_id/site_id/team_id only from an authoritative
                // shift-date-aware source. Do not infer current hierarchy.
            );
        }

        $next = count($rows) === $limit ? (string)end($rows)->id : null;
        return $this->json(array('items' => $items, 'next_cursor' => $next));
    }

    public function actionActivities()
    {
        $rawIds = Yii::app()->request->getQuery('login_session_ids', '');
        $ids = array_values(array_filter(array_map('intval', explode(',', $rawIds))));
        $cursor = (int)Yii::app()->request->getQuery('cursor', 0);
        $limit = min(
            max((int)Yii::app()->request->getQuery('limit', 500), 1),
            self::MAX_LIMIT
        );

        if (!$ids || count($ids) > 200) {
            return $this->json(array('error' => '1-200 login_session_ids are required'), 400);
        }

        $criteria = new CDbCriteria();
        $criteria->addInCondition('login_session_id', $ids);
        $criteria->addCondition('id > :cursor');
        $criteria->params[':cursor'] = $cursor;
        $criteria->order = 'id ASC';
        $criteria->limit = $limit;

        $rows = Activities::model()->findAll($criteria);
        $items = array();

        foreach ($rows as $row) {
            $items[] = array(
                'id' => (string)$row->id,
                'login_session_id' => (string)$row->login_session_id,
                'agent_id' => $row->agent_id,
                'data_source_id' => (int)$row->data_source_id,
                'activity_type_id' => (int)$row->activity_type_id,
                'source_id' => $row->source_id,
                'start_time' => $this->iso($row->start_time),
                'end_time' => $this->iso($row->end_time),
                'duration' => $row->duration,
                'inactivity_time' => (int)$row->inactivity_time,
                'campaign_id' => $row->campaign_id,
                'campaign_name' => $row->campaign_name,
                'client_id' => $row->client_id,
                'comment' => $row->comment,
                'created_at' => $this->iso($row->created_at),
                'updated_at' => $this->iso($row->updated_at),
                'computer_merged' => (int)$row->computer_merged,
            );
        }

        $next = count($rows) === $limit ? (string)end($rows)->id : null;
        return $this->json(array('items' => $items, 'next_cursor' => $next));
    }

    protected function validDate($value)
    {
        $d = DateTime::createFromFormat('Y-m-d', $value);
        return $d && $d->format('Y-m-d') === $value;
    }

    protected function iso($value)
    {
        if (!$value) {
            return null;
        }
        $d = new DateTime($value, new DateTimeZone('UTC'));
        return $d->format(DateTime::ATOM);
    }

    protected function json($payload, $status = 200)
    {
        http_response_code($status);
        header('Content-Type: application/json; charset=utf-8');
        echo CJSON::encode($payload);
        Yii::app()->end();
    }
}
