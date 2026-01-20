-- [ Global configuration ]
vim.g.mapleader = ' '
vim.g.maplocalleader = ' '

vim.o.number = true -- Show line numbers
vim.o.relativenumber = true -- Show relative line numbers

vim.o.breakindent = true
vim.o.shiftround = true -- Round indent to multiple of shiftwidth
vim.o.softtabstop = 4 -- Number of spaces for a tab when editing
vim.o.shiftwidth = 4 -- Number of spaces for autoindent
vim.o.expandtab = true -- Use spaces instead of tabs

vim.o.ignorecase = true -- Ignore case in search
vim.o.smartcase = true

vim.o.list = true -- Show whitespace characters
vim.o.confirm = true
vim.o.showmode = false

vim.o.timeoutlen = 300 -- Decrease mapped sequence wait time
vim.o.termguicolors = true -- Enable true colors
vim.o.inccommand = 'split' -- Shows the effects of a command incrementally in the buffer

vim.o.colorcolumn = '80' -- Highlight column 80
vim.o.signcolumn = 'yes' -- Always show sign column
vim.o.scrolloff = 4 -- Keep 8 lines above and below the cursor

vim.o.undofile = true -- Enable persistent undo
vim.o.swapfile = false -- Disable swap files

-- [ Custom keybinds ]
-- Allow qicker save and quit
vim.keymap.set('c', 'W', 'w', { desc = '(config): Save current file' })
vim.keymap.set('c', 'Q', 'q', { desc = '(config): Quit current window' })

-- Clear highlights on search when pressing <Esc> in normal mode
vim.keymap.set(
  'n',
  '<Esc>',
  '<cmd>nohlsearch<CR>',
  { desc = '(config): Clear search highlights' }
)

-- Nicer copy/paste operations
vim.keymap.set(
  'x',
  'p',
  '"_dP',
  { desc = '(config): Paste without overwriting register' }
)
vim.keymap.set('x', 'y', '"+y', { desc = '(config): Yank to system clipboard' })

-- Toggle text wrapping
vim.keymap.set(
  'n',
  '<leader>wr',
  '<cmd>set wrap!',
  { desc = '(config): Toggle text wrapping' }
)

-- Update plugins
vim.keymap.set(
  'n',
  '<leader>lv',
  '<cmd>Lazy sync<CR>',
  { desc = '(config): Lazy.nvim sync' }
)

-- LSP keymaps
vim.keymap.set(
  'n',
  'grd',
  vim.lsp.buf.definition,
  { desc = '(config): Go to defination' }
)
vim.keymap.set(
  'n',
  '<leader>q',
  vim.diagnostic.setloclist,
  { desc = '(config): Open diagnostic quickfix list' }
)

-- Keybinds to make split navigation easier. Use CTRL+<hjkl> to switch between windows
vim.keymap.set(
  'n',
  '<C-h>',
  '<C-w><C-h>',
  { desc = '(config): Move focus to the left window' }
)
vim.keymap.set(
  'n',
  '<C-l>',
  '<C-w><C-l>',
  { desc = '(config): Move focus to the right window' }
)
vim.keymap.set(
  'n',
  '<C-j>',
  '<C-w><C-j>',
  { desc = '(config): Move focus to the lower window' }
)
vim.keymap.set(
  'n',
  '<C-k>',
  '<C-w><C-k>',
  { desc = '(config): Move focus to the upper window' }
)

-- Toggle eol symbol in list mode
vim.o.listchars = 'tab:» ,trail:·,nbsp:␣'

vim.keymap.set('n', '<leader>nl', function()
  if string.find(vim.o.listchars, 'eol:') then
    vim.o.listchars = 'tab:» ,trail:·,nbsp:␣'
  else
    vim.o.listchars = 'tab:» ,trail:·,nbsp:␣,eol:⏎'
  end
end, { desc = '(config): Toggle "eol" symbol in list mode' })

-- Toggle format on save
vim.g.format_on_save = true

vim.keymap.set('n', '<leader>fg', function()
  vim.g.format_on_save = not vim.g.format_on_save
  print('format_on_save(global): ' .. tostring(vim.g.format_on_save))
end, { desc = '(config): Toggle "format_on_save" globally' })

vim.keymap.set('n', '<leader>fb', function()
  local output = ''
  if vim.g.format_on_save then
    if vim.b.format_on_save == nil then
      vim.b.format_on_save = not vim.g.format_on_save
    else
      vim.b.format_on_save = not vim.b.format_on_save
    end
    output = tostring(vim.b.format_on_save)
  else
    output = 'disabled globally'
  end
  print('format_on_save(buffer): ' .. output)
end, { desc = '(config): Toggle "format_on_save" for current buffer' })

-- [ Autocommands ]
-- Highlight when yanking (copying) text
vim.api.nvim_create_autocmd('TextYankPost', {
  desc = '(config): Highlight when yanking (copying) text',
  group = vim.api.nvim_create_augroup('highlight-yank', { clear = true }),
  callback = function()
    vim.hl.on_yank()
  end,
})

-- Switch indentation based on filetypes
vim.api.nvim_create_autocmd('FileType', {
  desc = '(config): Switch indentation on filetypes',
  group = vim.api.nvim_create_augroup('filetype-indent', { clear = true }),
  callback = function(event)
    local lang_map = { lua = 2, template = 2 }
    local indent = lang_map[event.match] or 4
    vim.o.softtabstop = indent
    vim.o.shiftwidth = indent
  end,
})

-- [ Plugins ]
local lazypath = vim.fn.stdpath 'data' .. '/lazy/lazy.nvim'
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  local lazyrepo = 'https://github.com/folke/lazy.nvim.git'
  local out = vim.fn.system {
    'git',
    'clone',
    '--filter=blob:none',
    '--branch=stable',
    lazyrepo,
    lazypath,
  }
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { 'Failed to clone lazy.nvim:\n', 'ErrorMsg' },
      { out, 'WarningMsg' },
      { '\nPress any key to exit...' },
    }, true, {})
    vim.fn.getchar()
    os.exit(1)
  end
end
vim.opt.rtp:prepend(lazypath)

require('lazy').setup {
  rocks = { enabled = false },
  spec = {

    {
      'folke/tokyonight.nvim',
      lazy = false,
      priority = 1000,
      --- @module 'tokyonight'
      --- @type tokyonight.Config
      ---@diagnostic disable-next-line: missing-fields
      opts = {
        transparent = true,
        dim_inactive = true,
      },
      config = function(_, opts)
        require('tokyonight').setup(opts)
        vim.cmd.colorscheme 'tokyonight-night'
      end,
    },

    {
      'nvim-lualine/lualine.nvim',
      dependencies = { 'nvim-tree/nvim-web-devicons' },
      opts = {
        options = {
          theme = 'tokyonight',
          component_separators = '|',
          section_separators = '',
        },
        sections = {
          -- Defaults
          -- lualine_a = {'mode'},
          -- lualine_x = { 'encoding', 'fileformat', 'filetype' },
          -- lualine_y = {'progress'},
          -- lualine_z = {'location'}
          lualine_a = { 'mode', '#vim.fn.getbufinfo({buflisted = 1})' },
          lualine_x = {
            'lsp_status',
            { 'copilot', show_colors = true },
            'encoding',
            'fileformat',
          },
          lualine_y = { 'filetype' },
          lualine_z = { 'progress', 'location' },
        },
      },
    },

    { 'AndreM222/copilot-lualine' },

    { 'folke/which-key.nvim', event = 'VeryLazy', opts = {} },

    { 'tpope/vim-fugitive', cmd = { 'Git' }, lazy = false },

    { 'lewis6991/gitsigns.nvim' },

    {
      'folke/zen-mode.nvim',
      cmd = { 'ZenMode' },
      dependencies = { { 'folke/twilight.nvim', opts = {} } },
      opts = {},
    },

    {
      'mbbill/undotree',
      cmd = { 'UndotreeToggle' },
      keys = {
        {
          '<leader>u',
          vim.cmd.UndotreeToggle,
          mode = '',
          desc = '(undotree): Toggle Undo Tree',
        },
      },
      opts = {},
    },

    {
      'stevearc/oil.nvim',
      ---@module 'oil'
      ---@type oil.SetupOpts
      opts = {},
      dependencies = { 'nvim-tree/nvim-web-devicons' },
      lazy = false,
    },

    {
      'folke/todo-comments.nvim',
      event = 'VimEnter',
      dependencies = { 'nvim-lua/plenary.nvim' },
      ---@module 'todo-comments'
      ---@type TodoOptions
      opts = { signs = false },
    },

    {
      'echasnovski/mini.nvim',
      version = false,
      config = function()
        require('mini.ai').setup()
        require('mini.surround').setup()
        require('mini.bracketed').setup()
      end,
    },

    {
      'zbirenbaum/copilot.lua',
      event = 'InsertEnter',
      cmd = { 'Copilot' },
      ---@module 'copilot'
      ---@type CopilotConfig
      ---@diagnostic disable: missing-fields
      opts = {
        suggestion = { enabled = false },
        panel = { enabled = false },
        filetypes = { markdown = true },
      },
      ---@diagnostic enable
    },

    {
      'folke/lazydev.nvim',
      ft = 'lua',
      ---@module 'lazydev'
      ---@type lazydev.Config
      opts = {
        library = {
          -- Load luvit types when the `vim.uv` word is found
          { path = '${3rd}/luv/library', words = { 'vim%.uv' } },
        },
      },
    },

    {
      'saghen/blink.cmp',
      event = 'VimEnter',
      version = '1.*',
      dependencies = {
        'folke/lazydev.nvim',
        'fang2hou/blink-copilot',
      },
      --- @module 'blink.cmp'
      --- @type blink.cmp.Config
      opts = {
        keymap = {
          preset = 'super-tab',
        },
        sources = {
          default = { 'lsp', 'path', 'buffer', 'lazydev', 'copilot' },
          providers = {
            copilot = {
              module = 'blink-copilot',
              score_offset = 100,
              async = true,
            },
            lazydev = {
              module = 'lazydev.integrations.blink',
              score_offset = 100,
            },
            buffer = {
              opts = {
                get_bufnrs = function()
                  return vim.tbl_filter(function(bufnr)
                    return vim.bo[bufnr].buftype == ''
                  end, vim.api.nvim_list_bufs())
                end,
              },
            },
          },
        },
        signature = { enabled = true },
        fuzzy = { implementation = 'prefer_rust_with_warning' },
        completion = {
          menu = {
            ---@diagnostic disable-next-line: assign-type-mismatch
            direction_priority = function()
              local ctx = require('blink.cmp').get_context()
              local item = require('blink.cmp').get_selected_item()
              if ctx == nil or item == nil then
                return { 's', 'n' }
              end

              local item_text = item.textEdit ~= nil and item.textEdit.newText
                or item.insertText
                or item.label
              local is_multi_line = item_text:find '\n' ~= nil

              -- after showing the menu upwards, we want to maintain that direction
              -- until we re-open the menu, so store the context id in a global variable
              if is_multi_line or vim.g.blink_cmp_upwards_ctx_id == ctx.id then
                vim.g.blink_cmp_upwards_ctx_id = ctx.id
                return { 'n', 's' }
              end
              return { 's', 'n' }
            end,
          },
          ghost_text = { enabled = true, show_without_selection = false },
        },
      },
    },

    {
      'nvim-telescope/telescope.nvim',
      event = 'VimEnter',
      dependencies = {
        'nvim-lua/plenary.nvim',
        'nvim-tree/nvim-web-devicons',
        'nvim-telescope/telescope-ui-select.nvim',
        {
          'nvim-telescope/telescope-fzf-native.nvim',
          build = 'make',
          cond = function()
            return vim.fn.executable 'make' == 1
          end,
        },
      },
      config = function()
        require('telescope').setup {
          extensions = {
            ['ui-select'] = {
              require('telescope.themes').get_dropdown(),
            },
          },
        }

        -- Enable Telescope extensions if they are installed
        pcall(require('telescope').load_extension, 'fzf')
        pcall(require('telescope').load_extension, 'ui-select')

        local builtin = require 'telescope.builtin'
        vim.keymap.set(
          'n',
          '<leader>sh',
          builtin.help_tags,
          { desc = '(telescope): Search help' }
        )
        vim.keymap.set(
          'n',
          '<leader>sk',
          builtin.keymaps,
          { desc = '(telescope): Search keymaps' }
        )
        vim.keymap.set(
          'n',
          '<leader>sf',
          builtin.find_files,
          { desc = '(telescope): Search files' }
        )
        vim.keymap.set(
          'n',
          '<leader>sw',
          builtin.grep_string,
          { desc = '(telescope): Search current word' }
        )
        vim.keymap.set(
          'n',
          '<leader>sg',
          builtin.live_grep,
          { desc = '(telescope): Search by grep' }
        )
        vim.keymap.set(
          'n',
          '<leader>sd',
          builtin.diagnostics,
          { desc = '(telescope): Search diagnostics' }
        )
        vim.keymap.set(
          'n',
          '<leader>sr',
          builtin.resume,
          { desc = '(telescope): Search resume' }
        )
        vim.keymap.set(
          'n',
          '<leader>s.',
          builtin.oldfiles,
          { desc = '(telescope): Search recent files ("." for repeat)' }
        )
        vim.keymap.set(
          'n',
          '<leader>/',
          builtin.current_buffer_fuzzy_find,
          { desc = '(telescope): Fuzzily search in current buffer' }
        )
        vim.keymap.set(
          'n',
          '<leader><leader>',
          builtin.buffers,
          { desc = '(telescope): Find existing buffers' }
        )
        vim.keymap.set('n', '<leader>s/', function()
          builtin.live_grep {
            grep_open_files = true,
            prompt_title = 'Live Grep in Open Files',
          }
        end, { desc = '(telescope): Search in open files' })
      end,
    },

    {
      'nvim-treesitter/nvim-treesitter',
      lazy = false,
      build = ':TSUpdate',
      config = function()
        local languages = {
          'bash',
          'diff',
          'query',
          'vim',
          'vimdoc',
          'lua',
          'luadoc',
          'markdown',
          'markdown_inline',
          'python',
          'yaml',
        }
        require('nvim-treesitter').install(languages)

        vim.api.nvim_create_autocmd('FileType', {
          pattern = languages,
          group = vim.api.nvim_create_augroup(
            'treesitter-features',
            { clear = true }
          ),
          callback = function()
            -- syntax highlighting, provided by Neovim
            vim.treesitter.start()
            -- folds, provided by Neovim
            -- vim.wo.foldexpr = 'v:lua.vim.treesitter.foldexpr()'
            -- vim.wo.foldmethod = 'expr'
            -- indentation, provided by nvim-treesitter
            -- vim.bo.indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
          end,
        })
      end,
    },

    {
      -- Main LSP Configuration
      'neovim/nvim-lspconfig',
      dependencies = {
        {
          'j-hui/fidget.nvim',
          opts = {
            notification = { override_vim_notify = true },
            -- window = { winblend = 0 },
          },
        },
        'saghen/blink.cmp',
      },
      config = function()
        -- Diagnostic Config
        vim.diagnostic.config {
          severity_sort = true,
          float = { source = 'if_many' },
          underline = { severity = vim.diagnostic.severity.ERROR },
          virtual_text = {
            source = 'if_many',
            spacing = 2,
          },
        }

        local servers = {
          'lua_ls',
          'ty',
        }

        for _, server_name in ipairs(servers) do
          vim.lsp.enable(server_name)
        end

        vim.api.nvim_create_autocmd('LspAttach', {
          group = vim.api.nvim_create_augroup(
            'config-lsp-attach',
            { clear = true }
          ),
          callback = function(event)
            local map = function(keys, func, desc, mode)
              mode = mode or 'n'
              vim.keymap.set(
                mode,
                keys,
                func,
                { buffer = event.buf, desc = desc }
              )
            end

            local builtin = require 'telescope.builtin'
            map('grD', vim.lsp.buf.declaration, '(lsp): Goto Declaration')
            map('grd', builtin.lsp_definitions, '(lsp): Goto Definition')
            map(
              'gW',
              builtin.lsp_dynamic_workspace_symbols,
              '(lsp): Open Workspace Symbols'
            )
            map('grr', builtin.lsp_references, '(lsp): Goto References')
            map(
              'gri',
              builtin.lsp_implementations,
              '(lsp): Goto Implementation'
            )
            map(
              'gO',
              builtin.lsp_document_symbols,
              '(lsp): Open Document Symbols'
            )
            map(
              'grt',
              builtin.lsp_type_definitions,
              '(lsp): Goto Type Definition'
            )

            -- The following code creates a keymap to toggle inlay hints in your
            -- code, if the language server you are using supports them
            local client = vim.lsp.get_client_by_id(event.data.client_id)
            if
              client
              and client:supports_method(
                vim.lsp.protocol.Methods.textDocument_inlayHint,
                event.buf
              )
            then
              map('<leader>th', function()
                vim.lsp.inlay_hint.enable(
                  not vim.lsp.inlay_hint.is_enabled { bufnr = event.buf }
                )
              end, '(lsp): Toggle Inlay Hints')
            end
          end,
        })
      end,
    },

    {
      'stevearc/conform.nvim',
      event = { 'BufWritePre' },
      cmd = { 'ConformInfo' },
      keys = {
        {
          '<leader>f',
          function()
            require('conform').format { async = true, lsp_format = 'fallback' }
          end,
          mode = '',
          desc = '(conform): Async format',
        },
      },
      ---@module 'conform'
      ---@type conform.setupOpts
      opts = {
        -- notify_on_error = false,
        format_on_save = function(bufnr)
          if vim.b[bufnr].format_on_save == nil then
            vim.b[bufnr].format_on_save = true
          end
          -- Disable with a global or buffer-local variable
          if not (vim.g.format_on_save and vim.b[bufnr].format_on_save) then
            return
          end
          -- Disable autoformat on certain filetypes
          local ignore_filetypes = { 'csv' }
          if vim.tbl_contains(ignore_filetypes, vim.bo[bufnr].filetype) then
            return
          end
          -- Disable autoformat for files in a certain path
          local bufname = vim.api.nvim_buf_get_name(bufnr)
          if bufname:match '/node_modules/' then
            return
          end
          return { timeout_ms = 500, lsp_format = 'fallback' }
        end,
        formatters_by_ft = {
          lua = { 'stylua' },
          python = { 'ruff' },
        },
      },
    },
  },
}
