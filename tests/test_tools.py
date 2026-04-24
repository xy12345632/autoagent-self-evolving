import pytest
from autoagent.tools.tool_registry import ToolRegistry


class TestToolRegistry:
    def test_singleton_pattern(self):
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()
        assert registry1 is registry2

    def test_register_tool(self, mock_tool_registry):
        def dummy_tool(input: str) -> str:
            return f"processed: {input}"

        mock_tool_registry.register_tool(
            "dummy_tool",
            dummy_tool,
            {"name": "dummy_tool", "description": "测试工具", "category": "testing"}
        )

        assert mock_tool_registry.has_tool("dummy_tool")
        assert mock_tool_registry.get_tool("dummy_tool") == dummy_tool

    def test_register_duplicate_tool(self, mock_tool_registry):
        def tool1():
            pass

        def tool2():
            pass

        mock_tool_registry.register_tool("dup_tool", tool1)
        mock_tool_registry.register_tool("dup_tool", tool2)

        assert mock_tool_registry.get_tool("dup_tool") == tool2

    def test_unregister_tool(self, mock_tool_registry):
        def test_tool():
            return "test"

        mock_tool_registry.register_tool("to_remove", test_tool)
        assert mock_tool_registry.has_tool("to_remove")

        result = mock_tool_registry.unregister_tool("to_remove")
        assert result is True
        assert not mock_tool_registry.has_tool("to_remove")

    def test_unregister_nonexistent_tool(self, mock_tool_registry):
        result = mock_tool_registry.unregister_tool("nonexistent")
        assert result is False

    def test_list_tools(self, mock_tool_registry):
        def tool_a():
            pass

        def tool_b():
            pass

        mock_tool_registry.register_tool("tool_a", tool_a)
        mock_tool_registry.register_tool("tool_b", tool_b)

        tools = mock_tool_registry.list_tools()
        assert "tool_a" in tools
        assert "tool_b" in tools

    def test_list_tools_by_category(self, mock_tool_registry):
        def web_tool():
            pass

        def sys_tool():
            pass

        mock_tool_registry.register_tool("web_search", web_tool, {"category": "web"})
        mock_tool_registry.register_tool("sys_execute", sys_tool, {"category": "system"})

        web_tools = mock_tool_registry.list_tools(category="web")
        assert "web_search" in web_tools
        assert "sys_execute" not in web_tools

    def test_get_categories(self, mock_tool_registry):
        mock_tool_registry.register_tool("tool1", lambda: None, {"category": "cat1"})
        mock_tool_registry.register_tool("tool2", lambda: None, {"category": "cat2"})
        mock_tool_registry.register_tool("tool3", lambda: None, {"category": "cat1"})

        categories = mock_tool_registry.get_categories()
        assert "cat1" in categories
        assert "cat2" in categories

    def test_get_tools_by_category(self, mock_tool_registry):
        mock_tool_registry.register_tool("t1", lambda: None, {"category": "web"})
        mock_tool_registry.register_tool("t2", lambda: None, {"category": "web"})
        mock_tool_registry.register_tool("t3", lambda: None, {"category": "system"})

        web_tools = mock_tool_registry.get_tools_by_category("web")
        assert len(web_tools) == 2
        assert "t1" in web_tools
        assert "t2" in web_tools

    def test_search_tools_by_name(self, mock_tool_registry):
        mock_tool_registry.register_tool("web_search", lambda: None, {"description": "搜索网页"})
        mock_tool_registry.register_tool("web_browse", lambda: None, {"description": "浏览网页"})

        results = mock_tool_registry.search_tools("search")
        assert "web_search" in results

    def test_search_tools_by_description(self, mock_tool_registry):
        mock_tool_registry.register_tool("file_read", lambda: None, {"description": "读取文件内容"})
        mock_tool_registry.register_tool("file_write", lambda: None, {"description": "写入文件内容"})

        results = mock_tool_registry.search_tools("读取")
        assert "file_read" in results

    def test_search_tools_by_tags(self, mock_tool_registry):
        mock_tool_registry.register_tool(
            "img_gen",
            lambda: None,
            {"tags": ["image", "generation", "ai"]}
        )

        results = mock_tool_registry.search_tools("image")
        assert "img_gen" in results

    def test_get_tool_schema(self, mock_tool_registry):
        schema = {
            "name": "test_schema",
            "description": "测试模式",
            "parameters": {"input": {"type": "string"}}
        }
        mock_tool_registry.register_tool("schema_tool", lambda: None, schema)

        retrieved = mock_tool_registry.get_tool_schema("schema_tool")
        assert retrieved == schema

    def test_update_tool_schema(self, mock_tool_registry):
        mock_tool_registry.register_tool("updatable", lambda: None, {"category": "old"})

        new_schema = {"category": "new", "description": "updated"}
        result = mock_tool_registry.update_tool_schema("updatable", new_schema)

        assert result is True
        categories = mock_tool_registry.get_categories()
        assert "old" not in categories or "updatable" not in mock_tool_registry.get_tools_by_category("old")

    def test_update_nonexistent_tool_schema(self, mock_tool_registry):
        result = mock_tool_registry.update_tool_schema("nonexistent", {"category": "test"})
        assert result is False

    def test_clear_registry(self, mock_tool_registry):
        mock_tool_registry.register_tool("t1", lambda: None)
        mock_tool_registry.register_tool("t2", lambda: None)

        mock_tool_registry.clear()
        assert mock_tool_registry.get_tool_count() == 0

    def test_get_all_schemas(self, mock_tool_registry):
        schema1 = {"name": "schema1"}
        schema2 = {"name": "schema2"}
        mock_tool_registry.register_tool("tool1", lambda: None, schema1)
        mock_tool_registry.register_tool("tool2", lambda: None, schema2)

        schemas = mock_tool_registry.get_all_schemas()
        assert len(schemas) == 2
        assert "tool1" in schemas
        assert "tool2" in schemas

    def test_get_registry_info(self, mock_tool_registry):
        mock_tool_registry.register_tool("tool1", lambda: None, {"category": "cat1"})
        mock_tool_registry.register_tool("tool2", lambda: None, {"category": "cat2"})

        info = mock_tool_registry.get_registry_info()
        assert info["total_tools"] == 2
        assert "cat1" in info["categories"]
        assert "cat2" in info["categories"]

    def test_get_tool_count(self, mock_tool_registry):
        assert mock_tool_registry.get_tool_count() == 0
        mock_tool_registry.register_tool("t1", lambda: None)
        assert mock_tool_registry.get_tool_count() == 1
        mock_tool_registry.register_tool("t2", lambda: None)
        assert mock_tool_registry.get_tool_count() == 2
