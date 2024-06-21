// Overall status
let el_sts_extension_down = document.getElementById("sts_extension_down");
let el_sts_sub_down = document.getElementById("sts_sub_down");
let el_sts_reboot_required = document.getElementById("sts_reboot_required");
let el_sts_waiting_for_reboot = document.getElementById("sts_waiting_for_reboot");

// MAVLink sensors
let el_sensor_ping = document.getElementById("sensor_ping");
let el_sensor_wl_dvl= document.getElementById("sensor_wl_dvl");

// Timeouts
let el_prb_rangefinder_timeout = document.getElementById("prb_rangefinder_timeout");
let el_prb_global_position_int_timeout = document.getElementById("prb_global_position_int_timeout");

// Errors
let el_prb_no_sensor_msgs = document.getElementById("prb_no_sensor_msgs");
let el_prb_too_many_sensor_msgs = document.getElementById("prb_too_many_sensor_msgs");
let el_prb_bad_type = document.getElementById("prb_bad_type");
let el_prb_bad_orient = document.getElementById("prb_bad_orient");

// Warnings
let el_prb_bad_max = document.getElementById("prb_bad_max");
let el_prb_bad_kpv = document.getElementById("prb_bad_kpv");
let el_prb_no_btn = document.getElementById("prb_no_btn");

// ArduSub state
let el_relative_alt_m_card = document.getElementById("relative_alt_m_card");
let el_rf_target_m_card = document.getElementById("rf_target_m_card");
let el_rangefinder_m_card = document.getElementById("rangefinder_m_card");
let el_seafloor_alt_m_card = document.getElementById("seafloor_alt_m_card");

// Parameter values
let el_rngfnd1_type_card = document.getElementById("rngfnd1_type_card");
let el_rngfnd1_max_cm_card = document.getElementById("rngfnd1_max_cm_card");
let el_rngfnd1_min_cm_card = document.getElementById("rngfnd1_min_cm_card");
let el_rngfnd1_orient_card = document.getElementById("rngfnd1_orient_card");
let el_surftrak_depth_card = document.getElementById("surftrak_depth_card");
let el_psc_jerk_z_card = document.getElementById("psc_jerk_z_card");
let el_pilot_accel_z_card = document.getElementById("pilot_accel_z_card");
let el_rngfnd_sq_min_card = document.getElementById("rngfnd_sq_min_card");
let el_btn_surftrak_card = document.getElementById("btn_surftrak_card");

const default_json = {
    "mav_state" : -1,  // -1 means BE is down, 0-2 are from the BE
    "reboot_required" : false,
    "ping" : null,
    "wl_dvl" : null,
    "prb_rangefinder_timeout" : false,
    "prb_global_position_int_timeout" : false,
    "relative_alt_m" : null,
    "rf_target_m" : null,
    "rangefinder_m" : null,
    "rngfnd1_type" : null,
    "rngfnd1_max_cm" : null,
    "rngfnd1_min_cm" : null,
    "rngfnd1_orient" : null,
    "surftrak_depth" : null,
    "psc_jerk_z" : null,
    "pilot_accel_z" : null,
    "rngfnd_sq_min" : null,
    "btn_surftrak" : null,
}

async function getStatus() {
    let response_json = default_json;

    // Get the latest status
    try {
        const response = await fetch("/status");
        if (response.ok) {
            response_json = await response.json();
        }
    } catch (ex) {
        console.error(ex)
    }

    const {
        mav_state,
        reboot_required,
        ping,
        wl_dvl,
        prb_rangefinder_timeout,
        prb_global_position_int_timeout,
        relative_alt_m,
        rf_target_m,
        rangefinder_m,
        rngfnd1_type,
        rngfnd1_max_cm,
        rngfnd1_min_cm,
        rngfnd1_orient,
        surftrak_depth,
        psc_jerk_z,
        pilot_accel_z,
        rngfnd_sq_min,
        btn_surftrak,
    } = response_json;

    // Overall status
    el_sts_extension_down.className = mav_state === -1 ? "status-shown" : "status-hidden";
    el_sts_sub_down.className = mav_state === 0 ? "status-shown" : "status-hidden";
    el_sts_reboot_required.className = reboot_required ? "status-shown" : "status-hidden";
    el_sts_waiting_for_reboot.className = mav_state === 2 ? "status-shown" : "status-hidden";

    // MAVLink sensors
    let num_sensors = 0;
    if (ping) {
        document.getElementById("ping_distance").textContent = (ping['distance'] * 0.01).toFixed(2);
        document.getElementById("ping_sq").textContent = (ping['sq']).toString();
        el_sensor_ping.className = "status-shown";
        ++num_sensors;
    } else {
        el_sensor_ping.className = "status-hidden";
    }
    if (wl_dvl) {
        document.getElementById("wl_dvl_distance").textContent = (wl_dvl['distance'] * 0.01).toFixed(2);
        document.getElementById("wl_dvl_sq").textContent = (wl_dvl['sq']).toString();
        el_sensor_wl_dvl.className = "status-shown";
        ++num_sensors;
    } else {
        el_sensor_wl_dvl.className = "status-hidden";
    }

    // Calc kpv, see https://github.com/clydemcqueen/ardusub_surftrak/ for definition
    let kpv = psc_jerk_z === null || pilot_accel_z === null ? 0 : 50 * psc_jerk_z / pilot_accel_z;

    // Timeouts
    el_prb_rangefinder_timeout.className = mav_state === 1 && prb_rangefinder_timeout ? "status-shown" : "status-hidden";
    el_prb_global_position_int_timeout.className = mav_state === 1 && prb_global_position_int_timeout ? "status-shown" : "status-hidden";

    // Errors
    el_prb_no_sensor_msgs.className = rngfnd1_type === 10 && num_sensors === 0 ? "status-shown" : "status-hidden";
    el_prb_too_many_sensor_msgs.className = rngfnd1_type === 10 && num_sensors > 1 ? "status-shown" : "status-hidden";
    el_prb_bad_type.className = rngfnd1_type === 0 || (rngfnd1_type !== 10 && num_sensors > 0) ? "status-shown" : "status-hidden";
    el_prb_bad_orient.className = rngfnd1_orient !== null && rngfnd1_orient !== 25 ? "status-shown" : "status-hidden";

    // Warnings
    el_prb_bad_max.className = rngfnd1_type !== null && rngfnd1_type !== 0 && rngfnd1_max_cm === 700 ? "status-shown" : "status-hidden";
    el_prb_bad_kpv.className = kpv > 1.0 ? "status-shown" : "status-hidden";
    el_prb_no_btn.className = mav_state === 1 && btn_surftrak === null ? "status-shown" : "status-hidden";

    // ArduSub state
    el_relative_alt_m_card.textContent = relative_alt_m != null ? relative_alt_m.toFixed(2) : "Unknown";
    el_rf_target_m_card.textContent = rf_target_m != null && rf_target_m > 0 ? rf_target_m.toFixed(2) : "No target";
    el_rangefinder_m_card.textContent = rangefinder_m != null ? rangefinder_m.toFixed(2) : "No rangefinder";
    el_seafloor_alt_m_card.textContent = relative_alt_m != null && rangefinder_m != null ? (relative_alt_m - rangefinder_m).toFixed(2) : "Unknown";

    // Parameter values
    el_rngfnd1_type_card.textContent = rngfnd1_type === null ? "Unknown" : rngfnd1_type;
    el_rngfnd1_max_cm_card.textContent = rngfnd1_max_cm === null ? "Unknown" : rngfnd1_max_cm;
    el_rngfnd1_min_cm_card.textContent = rngfnd1_min_cm === null ? "Unknown" : rngfnd1_min_cm;
    el_rngfnd1_orient_card.textContent = rngfnd1_orient === null ? "Unknown" : rngfnd1_orient;
    el_surftrak_depth_card.textContent = surftrak_depth === null ? "Unknown" : surftrak_depth;
    el_psc_jerk_z_card.textContent = psc_jerk_z === null ? "Unknown" : psc_jerk_z;
    el_pilot_accel_z_card.textContent = pilot_accel_z === null ? "Unknown" : pilot_accel_z;
    el_rngfnd_sq_min_card.textContent = rngfnd_sq_min === null ? "Unknown" : rngfnd_sq_min;
    el_btn_surftrak_card.textContent = btn_surftrak === null ? "No assignment" : btn_surftrak;
}

setInterval(getStatus, 500);

async function postFixit(fix) {
    try {
        const response = await fetch("/fixit", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({fix: fix}),
        });

        // TODO report result
        const result = await response.json();
    } catch (ex) {
        console.error(ex);
    }
}
