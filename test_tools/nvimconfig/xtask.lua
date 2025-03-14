local pickers = require "telescope.pickers"
local finders = require "telescope.finders"
local conf = require("telescope.config").values
local actions = require "telescope.actions"
local action_state = require "telescope.actions.state"
local sqlite = require("sqlite")

local db = sqlite.open("xtask.db")

-- fetch records
local sqlall = string.format("SELECT name FROM xtask ORDER BY ctime DESC")
local sqltsk = string.format('SELECT * FROM xtask WHERE id = [%d]', 1)
local xtasks = db:sql(sqlall)
print(xtasks)

-- our picker function
local xtasks = function(opts)
	opts = opts or {}
	pickers.new(opts, {
		prompt_title = "XTasks",
		finder = finders.new_table {
			results = xtasks,
			entry_maker = function(entry)
				return {
					value = entry,
					display = entry.name,
					ordinal = entry.id,
				}
			end,
		},
		sorter = conf.generic_sorter(opts),
		attach_mappings = function(prompt_bufnr, map)
			actions.select_default:replace(function()
				actions.close(prompt_bufnr)
				local selection = action_state.get_selected_entry()
				print(vim.inspect(selection))
				-- vim.api.nvim_put({ selection[1] }, "", false, true)
			end)
			return true
		end,

	}):find()
end

-- to execute the function
xtasks()

db:close()
