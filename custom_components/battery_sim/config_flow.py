"""Configuration flow for the Battery."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import CONF_NAME
from .const import (
    DOMAIN,
    BATTERY_OPTIONS,
    BATTERY_TYPE,
    CONF_BATTERY_SIZE,
    CONF_BATTERY_MAX_DISCHARGE_RATE,
    CONF_BATTERY_MAX_CHARGE_RATE,
    CONF_BATTERY_MAX_DISCHARGE_PERC,
    CONF_BATTERY_MAX_CHARGE_PERC,
    CONF_BATTERY_EFFICIENCY,
    CONF_UNIQUE_NAME,
    CONF_IMPORT_SENSOR,
    CONF_SECOND_IMPORT_SENSOR,
    CONF_EXPORT_SENSOR,
    CONF_SECOND_EXPORT_SENSOR,
    CONF_ENERGY_IMPORT_TARIFF,
    CONF_ENERGY_EXPORT_TARIFF,
    SETUP_TYPE,
    CONFIG_FLOW,
    METER_TYPE,
    ONE_IMPORT_ONE_EXPORT_METER,
    TWO_IMPORT_ONE_EXPORT_METER,
    TWO_IMPORT_TWO_EXPORT_METER,
    TARIFF_TYPE,
    NO_TARIFF_INFO,
    TARIFF_SENSOR_ENTITIES,
    FIXED_NUMERICAL_TARIFFS,
)


@config_entries.HANDLERS.register(DOMAIN)
class ExampleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Example config flow."""

    VERSION = 1

    def __init__(self):
        """Init the Battery Setup."""
        self._data = None

    async def async_step_user(self, user_input):
        """Handle a flow initialized by the user."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(BATTERY_TYPE):
                            vol.In(list(BATTERY_OPTIONS)),
                    }
                ),
            )

        if user_input[BATTERY_TYPE] == "Custom":
            return await self.async_step_custom()

        # Register Battery Option
        self._data = BATTERY_OPTIONS[user_input[BATTERY_TYPE]]
        self._data[SETUP_TYPE] = CONFIG_FLOW
        self._data[CONF_NAME] = f"{DOMAIN}: { user_input[BATTERY_TYPE]}"
        await self.async_set_unique_id(self._data[CONF_NAME])

        self._abort_if_unique_id_configured()
        return await self.async_step_metertype()

    async def async_step_custom(self, user_input=None):
        """Initialize Custom Battery."""
        if user_input is not None:
            self._data = user_input
            self._data[SETUP_TYPE] = CONFIG_FLOW
            self._data[CONF_NAME] = f"{DOMAIN}: {self._data[CONF_UNIQUE_NAME]}"
            await self.async_set_unique_id(self._data[CONF_NAME])
            self._abort_if_unique_id_configured()
            return await self.async_step_metertype()

        return self.async_show_form(
            step_id="custom",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_UNIQUE_NAME):
                        vol.All(str),
                    vol.Required(CONF_BATTERY_SIZE):
                        vol.All(vol.Coerce(float)),
                    vol.Required(CONF_BATTERY_MAX_DISCHARGE_RATE): vol.All(
                        vol.Coerce(float)
                    ),
                    vol.Required(CONF_BATTERY_MAX_CHARGE_RATE): vol.All(
                        vol.Coerce(float)
                    ),
                    vol.Required(
                        CONF_BATTERY_EFFICIENCY,
                        default=0.9
                    ): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=1)
                    ),
                }
            ),
        )

    async def async_step_metertype(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self._data[METER_TYPE] = user_input[METER_TYPE]
            self._data[TARIFF_TYPE] = user_input[TARIFF_TYPE]
            return await self.async_step_connectsensors()

        meter_types = [
            ONE_IMPORT_ONE_EXPORT_METER,
            TWO_IMPORT_ONE_EXPORT_METER,
            TWO_IMPORT_TWO_EXPORT_METER,
        ]
        tariff_types = [
            NO_TARIFF_INFO,
            FIXED_NUMERICAL_TARIFFS,
            TARIFF_SENSOR_ENTITIES
        ]

        return self.async_show_form(
            step_id="metertype",
            data_schema=vol.Schema(
                {
                    vol.Required(METER_TYPE): vol.In(meter_types),
                    vol.Required(TARIFF_TYPE): vol.In(tariff_types),
                }
            ),
        )

    async def async_step_connectsensors(self, user_input=None):
        """Connect Grid sensors."""
        if user_input is not None:
            self._data[CONF_IMPORT_SENSOR] = user_input[CONF_IMPORT_SENSOR]
            self._data[CONF_EXPORT_SENSOR] = user_input[CONF_EXPORT_SENSOR]

            if self._data[METER_TYPE] in [
                TWO_IMPORT_ONE_EXPORT_METER,
                TWO_IMPORT_TWO_EXPORT_METER
            ]:
                self._data[CONF_SECOND_IMPORT_SENSOR] = user_input[
                    CONF_SECOND_IMPORT_SENSOR
                ]

            if self._data[METER_TYPE] == TWO_IMPORT_TWO_EXPORT_METER:
                self._data[CONF_SECOND_EXPORT_SENSOR] = user_input[
                    CONF_SECOND_EXPORT_SENSOR
                ]

            if self._data[TARIFF_TYPE] == NO_TARIFF_INFO:
                return await self.async_step_chargeparameters()
            else:
                return await self.async_step_connecttariffsensors()

        schema: dict = {
            vol.Required(CONF_IMPORT_SENSOR): EntitySelector(
                EntitySelectorConfig(device_class=SensorDeviceClass.ENERGY)
            ),
            vol.Required(CONF_EXPORT_SENSOR): EntitySelector(
                EntitySelectorConfig(device_class=SensorDeviceClass.ENERGY)
            )
        }

        if self._data[METER_TYPE] in [
            TWO_IMPORT_ONE_EXPORT_METER,
            TWO_IMPORT_TWO_EXPORT_METER
        ]:
            schema[vol.Required(CONF_SECOND_IMPORT_SENSOR)] = (
                EntitySelector(
                    EntitySelectorConfig(device_class=SensorDeviceClass.ENERGY)
                )
            )

        if self._data[METER_TYPE] == TWO_IMPORT_TWO_EXPORT_METER:
            schema[vol.Required(CONF_SECOND_EXPORT_SENSOR)] = (
                EntitySelector(
                    EntitySelectorConfig(device_class=SensorDeviceClass.ENERGY)
                )
            )

        return self.async_show_form(
            step_id="connectsensors",
            data_schema=vol.Schema(schema)
        )

    async def async_step_connecttariffsensors(self, user_input=None):
        """Configure Tariff Sensors."""
        if user_input is not None:
            self._data[CONF_ENERGY_IMPORT_TARIFF] = user_input[
                CONF_ENERGY_IMPORT_TARIFF
            ]
            if CONF_ENERGY_EXPORT_TARIFF in user_input:
                self._data[CONF_ENERGY_EXPORT_TARIFF] = user_input[
                    CONF_ENERGY_EXPORT_TARIFF
                ]
            return await self.async_step_chargeparameters()

        if self._data[TARIFF_TYPE] == TARIFF_SENSOR_ENTITIES:
            schema = {
                vol.Required(CONF_ENERGY_IMPORT_TARIFF): EntitySelector(
                    EntitySelectorConfig()
                ),
                vol.Optional(CONF_ENERGY_EXPORT_TARIFF): EntitySelector(
                    EntitySelectorConfig()
                ),
            }
        elif self._data[TARIFF_TYPE] == FIXED_NUMERICAL_TARIFFS:
            schema = {
                vol.Required(CONF_ENERGY_IMPORT_TARIFF, default=0.3): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=10)
                ),
                vol.Optional(CONF_ENERGY_EXPORT_TARIFF, default=0.3): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=10)
                ),
            }

        return self.async_show_form(
            step_id="connecttariffsensors", data_schema=vol.Schema(schema)
        )

    async def async_step_chargeparameters(self, user_input=None):
        """Change Charge limits for the battery."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._data["name"],
                data=self._data
            )

        return self.async_show_form(
            step_id="chargeparameters",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BATTERY_MAX_DISCHARGE_PERC,
                        default=0.0
                    ): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=1)
                    ),
                    vol.Required(
                        CONF_BATTERY_MAX_CHARGE_PERC,
                        default=1.0
                    ): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=1)
                    ),
                }
            ),
        )
